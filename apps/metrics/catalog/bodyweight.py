from ..context import MetricContext
from ..formulas import linear_slope, moving_average
from ..registry import Category, Chart, MetricResult, Requires, Scope, metric

SMOOTHING_WINDOW = 7
MIN_ENTRIES = 2


@metric(
    key="bodyweight_trend",
    label="Tendencia de peso corporal",
    description=(
        "Tu ritmo real de cambio de peso en kilos por semana, calculado sobre una media móvil de "
        "siete días. La media suaviza las variaciones diarias de agua y comida, que pueden ser de "
        "más de un kilo y no significan nada."
    ),
    unit="kg/semana",
    category=Category.COMPOSITION,
    scope=Scope.USER,
    chart=Chart.LINE,
    higher_is_better=None,
    requires=(Requires.BODYWEIGHT,),
)
def bodyweight_trend(ctx: MetricContext) -> MetricResult:
    entries = ctx.weights
    if len(entries) < MIN_ENTRIES:
        return MetricResult(
            coverage=0.0,
            notes=["Registra tu peso al menos dos días para ver la tendencia."],
        )

    values = [float(entry.weight_kg) for entry in entries]
    window = min(SMOOTHING_WINDOW, len(values))
    smoothed = moving_average(values, window)

    series = [
        {"label": entry.date.isoformat(), "value": round(value, 2)}
        for entry, value in zip(entries, smoothed, strict=True)
        if value is not None
    ]

    first_date = entries[0].date
    points = [
        ((entry.date - first_date).days, value)
        for entry, value in zip(entries, smoothed, strict=True)
        if value is not None
    ]
    slope_per_day = linear_slope(points)

    notes = []
    if window < SMOOTHING_WINDOW:
        notes.append(
            f"Con {len(values)} registros la media se calcula sobre {window} días en vez de "
            f"{SMOOTHING_WINDOW}; el dato se afinará según registres más."
        )

    return MetricResult(
        value=round(slope_per_day * 7, 2) if slope_per_day is not None else None,
        series=series,
        coverage=1.0,
        notes=notes,
    )
