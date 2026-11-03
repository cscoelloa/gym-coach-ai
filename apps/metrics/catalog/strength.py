from collections import defaultdict

from ..context import MetricContext
from ..formulas import coverage_of, epley_1rm, linear_slope, week_key
from ..loads import effective_load
from ..registry import Category, Chart, MetricResult, Scope, metric

STALL_THRESHOLD_WEEKS = 4
MIN_SESSIONS_FOR_SLOPE = 3


def _e1rm_by_exercise_and_week(ctx: MetricContext) -> tuple[dict, int, int]:
    data: dict[str, dict[str, float]] = defaultdict(dict)
    usable = 0

    for set_log in ctx.working_sets:
        load = effective_load(set_log, ctx.latest_bodyweight)
        estimate = epley_1rm(float(load) if load is not None else None, set_log.reps)
        if estimate is None:
            continue

        usable += 1
        name = set_log.exercise.name
        week = week_key(set_log.session.date)
        if estimate > data[name].get(week, 0):
            data[name][week] = estimate

    return data, usable, len(ctx.working_sets)


@metric(
    key="e1rm_progression",
    label="Progresión de 1RM estimado",
    description=(
        "Cuánto ha subido tu fuerza en cada ejercicio, comparando el primer 1RM estimado del "
        "periodo con el último. Se calcula con la fórmula de Epley y solo con series de 12 "
        "repeticiones o menos, donde la estimación es fiable."
    ),
    unit="kg",
    category=Category.STRENGTH,
    scope=Scope.EXERCISE,
    chart=Chart.TABLE,
    higher_is_better=True,
)
def e1rm_progression(ctx: MetricContext) -> MetricResult:
    data, usable, total = _e1rm_by_exercise_and_week(ctx)

    rows = []
    for name, by_week in data.items():
        weeks = sorted(by_week)
        if len(weeks) < 2:
            continue
        first, last = by_week[weeks[0]], by_week[weeks[-1]]
        rows.append([name, round(first, 1), round(last, 1), round(last - first, 1)])

    rows.sort(key=lambda row: row[3], reverse=True)

    return MetricResult(
        value=round(sum(row[3] for row in rows) / len(rows), 1) if rows else None,
        columns=["Ejercicio", "Primero", "Último", "Cambio"],
        rows=rows,
        coverage=coverage_of(usable, total),
        notes=[] if rows else ["Hacen falta al menos dos semanas de datos por ejercicio."],
    )


@metric(
    key="personal_records",
    label="Récords personales",
    description=(
        "Tu mejor marca en cada ejercicio: más peso movido, más repeticiones y mejor 1RM estimado, "
        "con la fecha en que lo conseguiste."
    ),
    unit="kg / reps",
    category=Category.STRENGTH,
    scope=Scope.EXERCISE,
    chart=Chart.TABLE,
    higher_is_better=True,
)
def personal_records(ctx: MetricContext) -> MetricResult:
    best: dict[str, dict] = {}
    usable = 0

    for set_log in ctx.working_sets:
        load = effective_load(set_log, ctx.latest_bodyweight)
        if load is None or not set_log.reps:
            continue

        usable += 1
        name = set_log.exercise.name
        record = best.setdefault(
            name, {"weight": 0.0, "reps": 0, "e1rm": 0.0, "date": set_log.session.date}
        )

        if float(load) > record["weight"]:
            record["weight"] = float(load)
            record["date"] = set_log.session.date
        record["reps"] = max(record["reps"], set_log.reps)

        estimate = epley_1rm(float(load), set_log.reps)
        if estimate and estimate > record["e1rm"]:
            record["e1rm"] = estimate

    rows = [
        [
            name,
            round(record["weight"], 1),
            record["reps"],
            round(record["e1rm"], 1) if record["e1rm"] else "—",
            record["date"],
        ]
        for name, record in sorted(best.items())
    ]

    return MetricResult(
        value=len(rows),
        columns=["Ejercicio", "Mejor peso", "Más reps", "Mejor 1RM est.", "Fecha"],
        rows=rows,
        coverage=coverage_of(usable, len(ctx.working_sets)),
    )


@metric(
    key="progression_slope",
    label="Ritmo de progresión",
    description=(
        "A qué velocidad sube tu 1RM estimado en cada ejercicio, en kilos por semana. Un valor "
        "cercano a cero o negativo indica que ese ejercicio lleva tiempo sin avanzar."
    ),
    unit="kg/semana",
    category=Category.STRENGTH,
    scope=Scope.EXERCISE,
    chart=Chart.TABLE,
    higher_is_better=True,
)
def progression_slope(ctx: MetricContext) -> MetricResult:
    data, usable, total = _e1rm_by_exercise_and_week(ctx)

    rows = []
    for name, by_week in data.items():
        weeks = sorted(by_week)
        if len(weeks) < MIN_SESSIONS_FOR_SLOPE:
            continue
        points = [(float(index), by_week[week]) for index, week in enumerate(weeks)]
        slope = linear_slope(points)
        if slope is not None:
            rows.append([name, round(slope, 2), len(weeks)])

    rows.sort(key=lambda row: row[1])

    return MetricResult(
        value=round(sum(row[1] for row in rows) / len(rows), 2) if rows else None,
        columns=["Ejercicio", "kg/semana", "Semanas"],
        rows=rows,
        coverage=coverage_of(usable, total),
        notes=(
            []
            if rows
            else [f"Hacen falta al menos {MIN_SESSIONS_FOR_SLOPE} semanas por ejercicio."]
        ),
    )


@metric(
    key="stalled_exercises",
    label="Ejercicios estancados",
    description=(
        f"Ejercicios en los que no has batido tu 1RM estimado en {STALL_THRESHOLD_WEEKS} semanas o "
        "más. Son los primeros candidatos a cambiar de rango de repeticiones, de variante o a una "
        "semana de descarga."
    ),
    unit="ejercicios",
    category=Category.STRENGTH,
    scope=Scope.EXERCISE,
    chart=Chart.TABLE,
    higher_is_better=False,
)
def stalled_exercises(ctx: MetricContext) -> MetricResult:
    data, usable, total = _e1rm_by_exercise_and_week(ctx)

    rows = []
    for name, by_week in data.items():
        weeks = sorted(by_week)
        if len(weeks) < 2:
            continue

        best_value = max(by_week.values())
        best_week = next(week for week in weeks if by_week[week] == best_value)
        weeks_since = len(weeks) - 1 - weeks.index(best_week)

        if weeks_since >= STALL_THRESHOLD_WEEKS:
            rows.append([name, weeks_since, round(best_value, 1)])

    rows.sort(key=lambda row: row[1], reverse=True)

    return MetricResult(
        value=len(rows),
        columns=["Ejercicio", "Semanas sin récord", "Mejor 1RM est."],
        rows=rows,
        coverage=coverage_of(usable, total),
        notes=["Sin estancamientos detectados."] if not rows and usable else [],
    )
