from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ..models import AIGeneration, GenerationKind, GenerationStatus


class QuotaExceeded(Exception):
    pass


def check_quota(user, kind: str) -> None:
    if kind == GenerationKind.ROUTINE:
        _check(
            user, kind,
            per_hour=settings.AI_RATE_LIMIT_GENERATION_PER_HOUR,
            per_day=settings.AI_RATE_LIMIT_GENERATION_PER_DAY,
        )
    else:
        _check(user, kind, per_hour=settings.AI_RATE_LIMIT_ANALYSIS_PER_HOUR, per_day=None)


def _check(user, kind: str, *, per_hour: int, per_day: int | None) -> None:
    now = timezone.now()

    base = AIGeneration.objects.filter(user=user, kind=kind).exclude(
        status=GenerationStatus.ERROR
    )

    used_hour = base.filter(created_at__gte=now - timedelta(hours=1)).count()
    if used_hour >= per_hour:
        raise QuotaExceeded(
            f"Has alcanzado el límite de {per_hour} generaciones por hora. "
            "Inténtalo de nuevo más tarde."
        )

    if per_day is not None:
        used_day = base.filter(created_at__gte=now - timedelta(days=1)).count()
        if used_day >= per_day:
            raise QuotaExceeded(
                f"Has alcanzado el límite de {per_day} generaciones diarias."
            )


def remaining(user, kind: str) -> int:
    per_hour = (
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR
        if kind == GenerationKind.ROUTINE
        else settings.AI_RATE_LIMIT_ANALYSIS_PER_HOUR
    )
    used = (
        AIGeneration.objects.filter(
            user=user, kind=kind, created_at__gte=timezone.now() - timedelta(hours=1)
        )
        .exclude(status=GenerationStatus.ERROR)
        .count()
    )
    return max(0, per_hour - used)
