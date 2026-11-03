from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from apps.metrics.loads import is_working_set

from .models import SetLog
from .taxonomy import Equipment

LOAD_INCREMENT_KG = {
    Equipment.BARBELL: Decimal("2.5"),
    Equipment.OLYMPIC_BARBELL: Decimal("2.5"),
    Equipment.EZ_BARBELL: Decimal("2.5"),
    Equipment.TRAP_BAR: Decimal("2.5"),
    Equipment.SMITH_MACHINE: Decimal("2.5"),
    Equipment.DUMBBELL: Decimal("2"),
    Equipment.KETTLEBELL: Decimal("2"),
    Equipment.CABLE: Decimal("5"),
    Equipment.LEVERAGE_MACHINE: Decimal("5"),
    Equipment.HAMMER: Decimal("5"),
}


@dataclass(frozen=True)
class Performance:
    date: date
    sets: list[tuple[Decimal | None, int | None]]
    per_side: bool = False

    @property
    def summary(self) -> str:
        series = ", ".join(
            f"{format_kg(peso)}×{reps}" if peso is not None else f"{reps}"
            for peso, reps in self.sets
            if reps is not None
        )
        return f"{series} por lado" if series and self.per_side else series


def format_kg(valor: Decimal | None) -> str:
    if valor is None:
        return ""
    entero = valor.to_integral_value()
    return str(entero if valor == entero else valor.normalize())


def last_performance(user, exercise, before_session=None) -> Performance | None:
    consulta = SetLog.objects.filter(session__user=user, exercise=exercise).select_related(
        "session", "exercise"
    )
    if before_session is not None:
        consulta = consulta.exclude(session_id=before_session.pk)

    ultima = consulta.order_by("-session__date", "-session_id").first()
    if ultima is None:
        return None

    series = [
        (s.weight_kg, s.reps)
        for s in consulta.filter(session_id=ultima.session_id).order_by("set_number")
        if is_working_set(s)
    ]
    if not series:
        return None

    return Performance(
        date=ultima.session.date, sets=series, per_side=exercise.is_unilateral
    )


def best_set(user, exercise) -> Decimal | None:
    mejor = None
    series = SetLog.objects.filter(session__user=user, exercise=exercise).select_related("exercise")
    for s in series:
        if not is_working_set(s) or s.weight_kg is None:
            continue
        if mejor is None or s.weight_kg > mejor:
            mejor = s.weight_kg
    return mejor


def progression_hint(
    user, exercise, target_reps_max: int | None, before_session=None
) -> str | None:
    if not target_reps_max:
        return None

    anterior = last_performance(user, exercise, before_session=before_session)
    if anterior is None:
        return None

    completadas = [reps for _, reps in anterior.sets if reps is not None]
    if not completadas or any(reps < target_reps_max for reps in completadas):
        return None

    if exercise.is_bodyweight:
        return "La última vez completaste todas las repeticiones — prueba a añadir una más."

    pesos = [peso for peso, _ in anterior.sets if peso is not None]
    if not pesos:
        return None

    incremento = LOAD_INCREMENT_KG.get(exercise.equipment)
    if incremento is None:
        return "La última vez completaste todas las repeticiones — toca subir un punto."

    propuesta = max(pesos) + incremento
    return (
        f"La última vez completaste todas las repeticiones — prueba {format_kg(propuesta)} kg."
    )
