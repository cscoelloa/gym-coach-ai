import logging

from apps.metrics.context import DEFAULT_WEEKS
from apps.metrics.services import for_ai as metrics_for_ai
from apps.notifications.models import NotificationKind, Severity
from apps.notifications.services import notify
from apps.workouts.models import Program, WorkoutSession

from ..models import AIGeneration, GenerationKind, GenerationStatus, PromptKey
from ..providers import ProviderError, ProviderRefusal, get_provider
from ..providers.factory import active_vector_store_ids
from ..schemas import ProgressAnalysis
from . import prompts
from .limits import check_quota

logger = logging.getLogger(__name__)

MIN_SESSIONS = 6


class NotEnoughData(Exception):
    pass


class AnalysisFailed(Exception):
    pass


def analyze_progress(user, *, weeks: int = DEFAULT_WEEKS) -> AIGeneration:
    sessions = WorkoutSession.objects.filter(user=user).count()
    if sessions < MIN_SESSIONS:
        raise NotEnoughData(
            f"Hacen falta al menos {MIN_SESSIONS} entrenamientos registrados para analizar tu "
            f"progreso. Llevas {sessions}."
        )

    check_quota(user, GenerationKind.PROGRESS)

    computed = metrics_for_ai(user, weeks=weeks)
    prompt = prompts.get_prompt(PromptKey.PROGRESS_ANALYSIS)
    provider = get_provider()

    context = {
        "perfil": prompts.format_profile(user),
        "semanas": weeks,
        "metricas": prompts.format_metrics(computed),
        "rutina_actual": prompts.as_data(
            _describe_routine(user), "rutina_actual", max_chars=4000
        ),
    }
    system, user_message = prompts.render(prompt, context)

    try:
        result = provider.generate_structured(
            system=system,
            user=user_message,
            schema=ProgressAnalysis,
            vector_store_ids=active_vector_store_ids() if provider.supports_rag else None,
        )
    except ProviderRefusal as exc:
        _log_failure(user, provider, GenerationStatus.REFUSED, str(exc))
        raise AnalysisFailed(f"El modelo rechazó la petición: {exc}") from exc
    except ProviderError as exc:
        _log_failure(user, provider, GenerationStatus.ERROR, str(exc))
        raise AnalysisFailed(f"Fallo al hablar con el proveedor: {exc}") from exc

    return AIGeneration.objects.create(
        user=user,
        kind=GenerationKind.PROGRESS,
        provider=provider.config.provider,
        model=provider.model,
        prompt_rendered=f"{system}\n\n---\n\n{user_message}",
        raw_response=result.raw_text,
        parsed_output=result.parsed.model_dump(),
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        status=GenerationStatus.OK,
    )


def notify_progress(generation: AIGeneration):
    analysis = ProgressAnalysis.model_validate(generation.parsed_output)

    if analysis.stalled:
        nombres = ", ".join(item.exercise for item in analysis.stalled[:3])
        return notify(
            generation.user,
            kind=NotificationKind.STALL_DETECTED,
            severity=Severity.WARNING,
            title=f"Estancamiento en {len(analysis.stalled)} ejercicio(s)",
            body=f"{analysis.summary}\n\nSin progresar: {nombres}.",
            payload=generation.parsed_output,
            generation=generation,
        )

    return notify(
        generation.user,
        kind=NotificationKind.PROGRESS_READY,
        title="Tu análisis de progreso está listo",
        body=analysis.summary,
        payload=generation.parsed_output,
        generation=generation,
    )


def _describe_routine(user) -> str:
    program = (
        Program.objects.filter(user=user, is_active=True)
        .prefetch_related("schedule__routine__exercises__exercise")
        .order_by("-created_at")
        .first()
    )
    if program is None:
        return "Sin programa activo."

    lineas = [f"Programa: {program.name}", "", "Semana:"]
    rutinas = {}
    for entrada in program.schedule.all():
        if entrada.routine is None:
            lineas.append(f"- {entrada.get_weekday_display()}: descanso")
            continue
        lineas.append(f"- {entrada.get_weekday_display()}: {entrada.routine.name}")
        rutinas.setdefault(entrada.routine.pk, entrada.routine)

    for rutina in rutinas.values():
        ejercicios = ", ".join(
            f"{item.exercise.name} {item.target_sets}×{item.target_reps_min}-{item.target_reps_max}"
            for item in rutina.exercises.all()
        )
        lineas += ["", f"Rutina «{rutina.name}»: {ejercicios or 'sin ejercicios'}"]

    return "\n".join(lineas)


def _log_failure(user, provider, status, error):
    AIGeneration.objects.create(
        user=user,
        kind=GenerationKind.PROGRESS,
        provider=provider.config.provider,
        model=provider.model,
        status=status,
        error=error[:2000],
    )
