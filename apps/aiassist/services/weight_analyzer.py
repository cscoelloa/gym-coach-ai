import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.catalog.bodyweight import bodyweight_trend
from apps.metrics.context import MetricContext
from apps.notifications.models import NotificationKind, Severity
from apps.notifications.services import notify

from ..models import AIGeneration, GenerationKind, GenerationStatus, PromptKey
from ..providers import ProviderError, ProviderRefusal, get_provider
from ..schemas import WeightAnalysis
from . import prompts

logger = logging.getLogger(__name__)

MIN_ENTRIES = 7

TOLERANCE_KG_PER_WEEK = 0.2

COOLDOWN_DAYS = 7

DEFAULT_TARGETS = {"bulk": 0.25, "cut": -0.5, "maintain": 0.0}


class NoAnalysisNeeded(Exception):
    pass


def target_rate(user) -> float:
    if user.weekly_weight_change_target_kg is not None:
        return float(user.weekly_weight_change_target_kg)
    return DEFAULT_TARGETS.get(user.goal, 0.0)


def should_analyze(user) -> tuple[bool, str]:
    total = BodyWeightEntry.objects.filter(user=user).count()
    if total < MIN_ENTRIES:
        return False, f"solo hay {total} registros de peso (hacen falta {MIN_ENTRIES})"

    reciente = AIGeneration.objects.filter(
        user=user,
        kind=GenerationKind.WEIGHT,
        status=GenerationStatus.OK,
        created_at__gte=timezone.now() - timedelta(days=COOLDOWN_DAYS),
    ).exists()
    if reciente:
        return False, f"ya se analizó en los últimos {COOLDOWN_DAYS} días"

    result = bodyweight_trend(MetricContext(user=user))
    if result.value is None:
        return False, "todavía no se puede calcular una tendencia"

    desviacion = abs(result.value - target_rate(user))
    if desviacion <= TOLERANCE_KG_PER_WEEK:
        return False, "el ritmo va acorde al objetivo"

    return True, "el ritmo se aparta del objetivo"


def analyze_weight(user) -> AIGeneration:
    entries = list(
        BodyWeightEntry.objects.filter(user=user).order_by("-date")[:2]
    )
    if not entries:
        raise NoAnalysisNeeded("Sin registros de peso.")

    trend = bodyweight_trend(MetricContext(user=user))
    prompt = prompts.get_prompt(PromptKey.WEIGHT_ANALYSIS)
    provider = get_provider()

    anterior = entries[1] if len(entries) > 1 else None
    context = {
        "perfil": prompts.format_profile(user),
        "objetivo": user.get_goal_display(),
        "objetivo_semanal": f"{target_rate(user):+.2f} kg/semana",
        "peso_actual": f"{entries[0].weight_kg} kg ({entries[0].date})",
        "peso_anterior": (
            f"{anterior.weight_kg} kg ({anterior.date})" if anterior else "sin registro previo"
        ),
        "tendencia": (
            f"{trend.value:+.2f} kg/semana sobre media móvil de 7 días"
            if trend.value is not None
            else "no calculable"
        ),
    }
    system, user_message = prompts.render(prompt, context)

    try:
        result = provider.generate_structured(
            system=system, user=user_message, schema=WeightAnalysis
        )
    except (ProviderRefusal, ProviderError) as exc:
        AIGeneration.objects.create(
            user=user, kind=GenerationKind.WEIGHT, provider=provider.config.provider,
            model=provider.model, status=GenerationStatus.ERROR, error=str(exc)[:2000],
        )
        raise

    return AIGeneration.objects.create(
        user=user,
        kind=GenerationKind.WEIGHT,
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


def notify_weight(generation: AIGeneration):
    analysis = WeightAnalysis.model_validate(generation.parsed_output)
    if analysis.on_track:
        return None

    cuerpo = analysis.message
    if analysis.recommendation:
        cuerpo += f"\n\n{analysis.recommendation}"

    return notify(
        generation.user,
        kind=NotificationKind.WEIGHT_OFF_TRACK,
        severity=Severity.WARNING,
        title="Tu peso no va acorde a tu objetivo",
        body=cuerpo,
        payload=generation.parsed_output,
        generation=generation,
    )


def decimal_or_none(value) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None
