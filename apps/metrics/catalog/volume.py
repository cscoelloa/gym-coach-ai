from collections import defaultdict

from ..context import MetricContext
from ..formulas import coverage_of, week_key, week_label
from ..loads import is_effective_set, muscle_contributions, total_work
from ..registry import Category, Chart, MetricResult, Requires, Scope, metric


def _muscle_series(ctx: MetricContext, totals: dict[str, float]) -> list[dict]:
    return [
        {"label": ctx.muscle_names.get(slug, slug), "value": round(total, 1)}
        for slug, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


@metric(
    key="weekly_volume_by_muscle",
    label="Volumen semanal por grupo muscular",
    description=(
        "Series por semana que recibe cada músculo. El músculo objetivo del ejercicio suma una "
        "serie completa y los secundarios media: un press de banca cuenta 1 para pectoral y 0,5 "
        "para tríceps y deltoides. Más no siempre es mejor — hay un punto en que el volumen extra "
        "solo añade fatiga."
    ),
    unit="series/semana",
    category=Category.VOLUME,
    scope=Scope.MUSCLE,
    chart=Chart.BAR,
    higher_is_better=None,
)
def weekly_volume_by_muscle(ctx: MetricContext) -> MetricResult:
    totals: dict[str, float] = defaultdict(float)

    for set_log in ctx.working_sets:
        for slug, weight in muscle_contributions(set_log.exercise).items():
            totals[slug] += weight

    per_week = {slug: total / ctx.weeks_in_window for slug, total in totals.items()}

    return MetricResult(
        value=round(sum(per_week.values()), 1) if per_week else None,
        series=_muscle_series(ctx, per_week),
        coverage=1.0 if ctx.working_sets else 0.0,
        notes=[] if ctx.working_sets else ["Todavía no hay series registradas."],
    )


@metric(
    key="effective_sets_by_muscle",
    label="Series efectivas por grupo muscular",
    description=(
        "Series por semana que llegan cerca del fallo. Cuentan todas tus series de trabajo, que "
        "es el «hard set» de la literatura: si alguna te quedó lejos del fallo, este número la "
        "cuenta igual."
    ),
    unit="series/semana",
    category=Category.VOLUME,
    scope=Scope.MUSCLE,
    chart=Chart.BAR,
    higher_is_better=None,
)
def effective_sets_by_muscle(ctx: MetricContext) -> MetricResult:
    totals: dict[str, float] = defaultdict(float)

    for set_log in ctx.working_sets:
        if not is_effective_set(set_log):
            continue
        for slug, weight in muscle_contributions(set_log.exercise).items():
            totals[slug] += weight

    per_week = {slug: total / ctx.weeks_in_window for slug, total in totals.items()}

    return MetricResult(
        value=round(sum(per_week.values()), 1) if per_week else None,
        series=_muscle_series(ctx, per_week),
    )


@metric(
    key="training_frequency_by_muscle",
    label="Frecuencia por grupo muscular",
    description=(
        "Cuántos días por semana estimulas cada músculo. Repartir el mismo volumen en más días "
        "suele dar mejores resultados que concentrarlo en una sola sesión."
    ),
    unit="días/semana",
    category=Category.VOLUME,
    scope=Scope.MUSCLE,
    chart=Chart.BAR,
    higher_is_better=None,
)
def training_frequency_by_muscle(ctx: MetricContext) -> MetricResult:
    days_by_muscle: dict[str, set] = defaultdict(set)

    for set_log in ctx.working_sets:
        for slug in muscle_contributions(set_log.exercise):
            days_by_muscle[slug].add(set_log.session.date)

    per_week = {
        slug: len(days) / ctx.weeks_in_window for slug, days in days_by_muscle.items()
    }

    return MetricResult(
        value=round(max(per_week.values()), 1) if per_week else None,
        series=_muscle_series(ctx, per_week),
        coverage=1.0 if ctx.working_sets else 0.0,
    )


@metric(
    key="weekly_tonnage",
    label="Tonelaje semanal",
    description=(
        "Carga total movida cada semana: peso × repeticiones, sumando todas las series. En los "
        "ejercicios de peso corporal se usa tu peso registrado como carga, más el lastre si lo "
        "hay. Sirve para ver que progresas aunque el peso de la barra no suba."
    ),
    unit="kg",
    category=Category.VOLUME,
    scope=Scope.USER,
    chart=Chart.LINE,
    higher_is_better=True,
    requires=(Requires.BODYWEIGHT,),
)
def weekly_tonnage(ctx: MetricContext) -> MetricResult:
    by_week: dict[str, float] = defaultdict(float)
    usable = 0
    missing_bodyweight = False

    for set_log in ctx.working_sets:
        load = total_work(set_log, ctx.latest_bodyweight)
        if load is None:
            missing_bodyweight = True
            continue
        if not set_log.reps:
            continue

        usable += 1
        by_week[week_key(set_log.session.date)] += float(load) * set_log.reps

    series = [
        {"label": week_label(week), "value": round(total)}
        for week, total in sorted(by_week.items())
    ]

    notes = []
    if missing_bodyweight:
        notes.append(
            "Algunas series de peso corporal no cuentan porque no tienes ningún peso registrado."
        )

    return MetricResult(
        value=round(sum(by_week.values()) / len(by_week)) if by_week else None,
        series=series,
        coverage=coverage_of(usable, len(ctx.working_sets)),
        notes=notes,
    )
