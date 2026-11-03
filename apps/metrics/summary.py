from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import Count
from django.utils import formats, timezone

from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import ScheduleEntry, SetLog, WorkoutSession
from apps.workouts.taxonomy import MUSCLE_ES, muscle_slug

from .loads import is_effective_set, muscle_contributions

WEEKDAY_INITIALS = ["L", "M", "X", "J", "V", "S", "D"]

INTENSITY_MINUTES = [30, 60, 90]

LEVEL_UNKNOWN_DURATION = 1

CALENDAR_MONTHS = 12
WEIGHT_DELTA_DAYS = 30


def _monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _planned_weekdays(user) -> set[int]:
    return set(
        ScheduleEntry.objects.filter(
            program__user=user, program__is_active=True, routine__isnull=False
        ).values_list("weekday", flat=True)
    )


@dataclass(frozen=True)
class WeekDay:
    date: date
    initial: str
    is_today: bool
    is_future: bool
    trained: bool
    planned: bool


def week_strip(user, on_date: date | None = None) -> list[WeekDay]:
    today = on_date or timezone.localdate()
    monday = _monday_of(today)
    sunday = monday + timedelta(days=6)

    trained = set(
        WorkoutSession.objects.filter(
            user=user, date__gte=monday, date__lte=sunday
        ).values_list("date", flat=True)
    )

    planned = _planned_weekdays(user)

    return [
        WeekDay(
            date=monday + timedelta(days=offset),
            initial=WEEKDAY_INITIALS[offset],
            is_today=(monday + timedelta(days=offset)) == today,
            is_future=(monday + timedelta(days=offset)) > today,
            trained=(monday + timedelta(days=offset)) in trained,
            planned=offset in planned,
        )
        for offset in range(7)
    ]


@dataclass(frozen=True)
class Streak:
    weeks: int
    this_week_done: int
    this_week_planned: int
    total_sessions: int


def streak(user, on_date: date | None = None) -> Streak:
    today = on_date or timezone.localdate()
    this_monday = _monday_of(today)

    semanas_con_sesion = {
        _monday_of(fecha)
        for fecha in WorkoutSession.objects.filter(user=user, date__lte=today).values_list(
            "date", flat=True
        )
    }

    cursor = this_monday if this_monday in semanas_con_sesion else this_monday - timedelta(weeks=1)
    weeks = 0
    while cursor in semanas_con_sesion:
        weeks += 1
        cursor -= timedelta(weeks=1)

    return Streak(
        weeks=weeks,
        this_week_done=WorkoutSession.objects.filter(
            user=user, date__gte=this_monday, date__lte=today
        ).count(),
        this_week_planned=len(_planned_weekdays(user)),
        total_sessions=WorkoutSession.objects.filter(user=user).count(),
    )


@dataclass(frozen=True)
class CalendarDay:
    date: date
    level: int
    minutes: int
    sessions: int


@dataclass(frozen=True)
class CalendarWeek:
    days: list[CalendarDay | None]
    label: str = ""


MIN_WEEKS_FOR_LABEL = 3


def _level_for(minutes: int, sessions: int) -> int:
    if not sessions:
        return 0
    if not minutes:
        return LEVEL_UNKNOWN_DURATION
    for nivel, corte in enumerate(INTENSITY_MINUTES, start=1):
        if minutes < corte:
            return nivel
    return len(INTENSITY_MINUTES) + 1


def activity_calendar(user, months: int = CALENDAR_MONTHS, on_date: date | None = None) -> dict:
    today = on_date or timezone.localdate()
    desde = _monday_of(today - timedelta(days=int(months * 30.4)))

    por_dia: dict[date, list[int]] = defaultdict(lambda: [0, 0])
    consulta = WorkoutSession.objects.filter(user=user, date__gte=desde, date__lte=today).values(
        "date", "started_at", "finished_at"
    )
    for fila in consulta:
        acumulado = por_dia[fila["date"]]
        acumulado[1] += 1
        if fila["started_at"] and fila["finished_at"]:
            duracion = (fila["finished_at"] - fila["started_at"]).total_seconds() / 60
            if duracion > 0:
                acumulado[0] += int(duracion)

    semanas: list[list[CalendarDay | None]] = []
    inicios: list[tuple[int, str]] = []
    cursor = desde
    mes_anterior = None

    while cursor <= today:
        columna: list[CalendarDay | None] = []
        for offset in range(7):
            dia = cursor + timedelta(days=offset)
            if dia > today:
                columna.append(None)
                continue
            minutos, sesiones = por_dia.get(dia, (0, 0))
            columna.append(
                CalendarDay(
                    date=dia,
                    level=_level_for(minutos, sesiones),
                    minutes=minutos,
                    sessions=sesiones,
                )
            )

        if cursor.month != mes_anterior:
            inicios.append((len(semanas), formats.date_format(cursor, "M")))
            mes_anterior = cursor.month

        semanas.append(columna)
        cursor += timedelta(weeks=1)

    etiquetas = [""] * len(semanas)
    for orden, (columna_inicial, nombre) in enumerate(inicios):
        siguiente = inicios[orden + 1][0] if orden + 1 < len(inicios) else len(semanas)
        if siguiente - columna_inicial >= MIN_WEEKS_FOR_LABEL:
            etiquetas[columna_inicial] = nombre

    return {
        "weeks": [
            CalendarWeek(days=columna, label=etiqueta)
            for columna, etiqueta in zip(semanas, etiquetas, strict=True)
        ],
        "levels": list(range(len(INTENSITY_MINUTES) + 2)),
    }


def headline_tiles(user, on_date: date | None = None) -> dict:
    today = on_date or timezone.localdate()
    racha = streak(user, on_date=today)

    del_mes = WorkoutSession.objects.filter(
        user=user, date__year=today.year, date__month=today.month
    ).count()

    return {
        "total_sessions": racha.total_sessions,
        "sessions_this_month": del_mes,
        "streak_weeks": racha.weeks,
        "weight_delta": weight_delta(user, days=WEIGHT_DELTA_DAYS, on_date=today),
    }


def weight_delta(user, days: int = WEIGHT_DELTA_DAYS, on_date: date | None = None):
    today = on_date or timezone.localdate()

    ultimo = (
        BodyWeightEntry.objects.filter(user=user, date__lte=today).order_by("-date").first()
    )
    if ultimo is None:
        return None

    anterior = (
        BodyWeightEntry.objects.filter(user=user, date__lte=today - timedelta(days=days))
        .order_by("-date")
        .first()
    )
    if anterior is None:
        return None

    return ultimo.weight_kg - anterior.weight_kg


EFFECTIVE_SETS_LEVELS = [5, 10, 15]


def _muscle_level(series: float) -> int:
    if series <= 0:
        return 0
    for nivel, corte in enumerate(EFFECTIVE_SETS_LEVELS, start=1):
        if series < corte:
            return nivel
    return len(EFFECTIVE_SETS_LEVELS) + 1


def muscle_map(user, weeks: int = 1, on_date: date | None = None) -> dict:
    today = on_date or timezone.localdate()
    desde = _monday_of(today) - timedelta(weeks=weeks - 1)

    series: dict[str, float] = defaultdict(float)
    consulta = (
        SetLog.objects.filter(
            session__user=user, session__date__gte=desde, session__date__lte=today
        )
        .select_related("exercise", "exercise__target_muscle", "session")
        .prefetch_related("exercise__secondary_muscles")
    )
    for set_log in consulta:
        if not is_effective_set(set_log):
            continue
        for slug, peso in muscle_contributions(set_log.exercise).items():
            series[slug] += peso

    niveles = {
        muscle_slug(nombre): _muscle_level(series.get(muscle_slug(nombre), 0.0))
        for nombre in MUSCLE_ES
    }

    return {
        "levels": niveles,
        "sets": {slug: round(total, 1) for slug, total in series.items()},
        "since": desde,
        "total_sets": round(sum(series.values()), 1),
    }


def sessions_by_weekday(user, weeks: int = 12, on_date: date | None = None) -> dict[int, int]:
    today = on_date or timezone.localdate()
    desde = today - timedelta(weeks=weeks)

    filas = (
        WorkoutSession.objects.filter(user=user, date__gte=desde, date__lte=today)
        .values("date")
        .annotate(n=Count("id"))
    )
    por_dia: dict[int, int] = defaultdict(int)
    for fila in filas:
        por_dia[fila["date"].weekday()] += fila["n"]
    return dict(por_dia)
