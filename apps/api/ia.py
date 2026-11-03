import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aiassist.models import (
    AIGeneration,
    GenerationKind,
    GenerationStatus,
    Provider,
    TrainingGoal,
)
from apps.aiassist.providers import ProviderError
from apps.aiassist.schemas import ProgressAnalysis, RoutinePlan
from apps.aiassist.services import (
    GenerationFailed,
    NoCandidates,
    ProviderUnavailable,
    QuotaExceeded,
    UnusableOutput,
    apply_plan,
    generate_routine,
    programacion,
)
from apps.aiassist.services.limits import remaining
from apps.aiassist.services.progress_analyzer import (
    MIN_SESSIONS,
    AnalysisFailed,
    NotEnoughData,
    analyze_progress,
    notify_progress,
)
from apps.aiassist.services.prompts import MissingPrompt
from apps.aiassist.services.split import (
    MAX_EJERCICIOS,
    MAX_MUSCULOS_POR_DIA,
    MIN_EJERCICIOS,
    RepartoInvalido,
    conflictos_de_recuperacion,
    dias_sugeridos,
    parse_split,
)
from apps.workouts.catalog import musculos_entrenables
from apps.workouts.models import Exercise, Weekday, WorkoutSession

logger = logging.getLogger(__name__)

MAX_NOTAS = 1000


def _error(detalle: str, codigo: str, estado: int) -> Response:
    return Response({"detail": detalle, "codigo": codigo}, status=estado)


def _metadatos(generacion: AIGeneration) -> dict:
    return {
        "id": generacion.pk,
        "fecha": generacion.created_at.isoformat(),
        "proveedor": Provider(generacion.provider).label
        if generacion.provider in Provider.values
        else generacion.provider,
        "modelo": generacion.model,
        "latencia_ms": generacion.latency_ms,
        "tokens_entrada": generacion.input_tokens,
        "tokens_salida": generacion.output_tokens,
    }


def _propuesta(generacion: AIGeneration) -> dict:
    plan = RoutinePlan.model_validate(generacion.parsed_output)

    catalogo = {
        ejercicio.external_id: ejercicio
        for ejercicio in Exercise.objects.filter(
            external_id__in=[
                item.external_id for rutina in plan.routines for item in rutina.exercises
            ]
        ).select_related("target_muscle")
    }

    def ejercicio_de(item):
        encontrado = catalogo.get(item.external_id)
        return {
            "external_id": item.external_id,
            "nombre": encontrado.name if encontrado else item.external_id,
            "slug": encontrado.slug if encontrado else None,
            "imagen": encontrado.image.url if encontrado and encontrado.image else None,
            "en_catalogo": encontrado is not None,
            "series": item.sets,
            "reps_min": item.reps_min,
            "reps_max": item.reps_max,
            "descanso": item.rest_seconds,
        }

    por_nombre = {rutina.name.strip(): rutina.name for rutina in plan.routines}
    asignado = {dia.weekday: por_nombre.get(dia.routine_name.strip()) for dia in plan.schedule}

    return {
        "generacion": _metadatos(generacion),
        "nombre": plan.name,
        "descripcion": plan.description,
        "motivo": plan.rationale,
        "rutinas": [
            {
                "nombre": rutina.name,
                "ejercicios": [ejercicio_de(item) for item in rutina.exercises],
            }
            for rutina in plan.routines
        ],
        "semana": [
            {"weekday": weekday, "etiqueta": etiqueta, "rutina": asignado.get(weekday) or None}
            for weekday, etiqueta in Weekday.choices
        ],
        "ya_aplicada": generacion.programs.exists(),
    }


def _mia(request, pk) -> AIGeneration:
    return get_object_or_404(
        AIGeneration,
        pk=pk,
        user=request.user,
        kind=GenerationKind.ROUTINE,
        status=GenerationStatus.OK,
    )


class GenerarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "restantes": remaining(request.user, GenerationKind.ROUTINE),
            "dias_por_defecto": request.user.available_days_per_week,
            "tiene_equipamiento": bool(request.user.available_equipment),
            "musculos": [
                {"valor": slug, "etiqueta": etiqueta, "n": n}
                for slug, etiqueta, n in musculos_entrenables(request.user)
            ],
            "dias_sugeridos": dias_sugeridos(request.user.available_days_per_week),
            "ejercicios": {"min": MIN_EJERCICIOS, "max": MAX_EJERCICIOS, "por_defecto": 6},
            "max_musculos_por_dia": MAX_MUSCULOS_POR_DIA,
            "objetivos": [
                {
                    "valor": valor,
                    "etiqueta": etiqueta,
                    "resumen": programacion.resumen(programacion.reglas_de(valor)),
                }
                for valor, etiqueta in TrainingGoal.choices
            ],
            "objetivo_por_defecto": TrainingGoal.HYPERTROPHY,
        })

    def post(self, request):
        dias = request.data.get("days_per_week")
        try:
            dias = int(dias) if dias not in (None, "") else None
        except (TypeError, ValueError):
            dias = None
        if dias is not None and not 1 <= dias <= 7:
            return _error("Los días por semana van de 1 a 7.", "parametros", 400)

        notas = str(request.data.get("notes") or "")[:MAX_NOTAS]

        objetivo = str(request.data.get("training_goal") or TrainingGoal.HYPERTROPHY)
        if objetivo not in TrainingGoal.values:
            return _error(
                f"«{objetivo}» no es un objetivo de entrenamiento.",
                "parametros",
                status.HTTP_400_BAD_REQUEST,
            )

        reparto = None
        if (crudo := request.data.get("split")) is not None:
            try:
                reparto = parse_split(crudo, user=request.user)
            except RepartoInvalido as exc:
                return _error(str(exc), "reparto", status.HTTP_400_BAD_REQUEST)
            if conflictos := conflictos_de_recuperacion(reparto):
                return _error(" ".join(conflictos), "descanso", status.HTTP_400_BAD_REQUEST)

        try:
            generacion = generate_routine(
                request.user,
                notes=notas,
                days_per_week=dias,
                split=reparto,
                training_goal=objetivo,
            )
        except QuotaExceeded as exc:
            return _error(str(exc), "cuota", status.HTTP_429_TOO_MANY_REQUESTS)
        except NoCandidates as exc:
            return _error(str(exc), "sin_candidatos", status.HTTP_409_CONFLICT)
        except (MissingPrompt, ProviderError, ProviderUnavailable, UnusableOutput) as exc:
            return _error(str(exc), "proveedor", status.HTTP_502_BAD_GATEWAY)

        return Response(_propuesta(generacion), status=status.HTTP_201_CREATED)


class PropuestaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response(_propuesta(_mia(request, pk)))


class AceptarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        generacion = _mia(request, pk)
        try:
            programa = apply_plan(generacion)
        except GenerationFailed as exc:
            return _error(str(exc), "no_aplicable", status.HTTP_409_CONFLICT)

        return Response(
            {"programa": {"id": programa.pk, "nombre": programa.name}},
            status=status.HTTP_201_CREATED,
        )


class DescartarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        generacion = _mia(request, pk)
        logger.info("Generación %s descartada por el usuario", generacion.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnalisisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(self._estado(request.user))

    def post(self, request):
        try:
            generacion = analyze_progress(request.user)
        except NotEnoughData as exc:
            return _error(str(exc), "sin_datos", status.HTTP_409_CONFLICT)
        except QuotaExceeded as exc:
            return _error(str(exc), "cuota", status.HTTP_429_TOO_MANY_REQUESTS)
        except (MissingPrompt, ProviderError, AnalysisFailed) as exc:
            return _error(str(exc), "proveedor", status.HTTP_502_BAD_GATEWAY)

        notify_progress(generacion)
        return Response(self._estado(request.user), status=status.HTTP_201_CREATED)

    def _estado(self, user) -> dict:
        ultimo = (
            AIGeneration.objects.filter(
                user=user, kind=GenerationKind.PROGRESS, status=GenerationStatus.OK
            )
            .order_by("-created_at")
            .first()
        )
        sesiones = WorkoutSession.objects.filter(user=user).count()

        return {
            "restantes": remaining(user, GenerationKind.PROGRESS),
            "sesiones": sesiones,
            "sesiones_necesarias": MIN_SESSIONS,
            "generacion": _metadatos(ultimo) if ultimo else None,
            "analisis": (
                ProgressAnalysis.model_validate(ultimo.parsed_output).model_dump()
                if ultimo
                else None
            ),
        }
