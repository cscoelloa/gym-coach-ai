from collections import defaultdict

from ..context import MetricContext
from ..formulas import coverage_of, week_key, week_label
from ..loads import total_work
from ..registry import Category, Chart, MetricResult, Requires, Scope, metric


@metric(
    key="adherence_rate",
    label="Adherencia",
    description=(
        "Qué porcentaje de los entrenamientos que planificaste has hecho realmente. Se compara con "
        "los días no marcados como descanso de tu rutina activa."
    ),
    unit="%",
    category=Category.CONSISTENCY,
    scope=Scope.USER,
    chart=Chart.LINE,
    higher_is_better=True,
    requires=(Requires.ROUTINE,),
)
def adherence_rate(ctx: MetricContext) -> MetricResult:
    planned = ctx.planned_days_per_week
    if not planned:
        return MetricResult(
            coverage=0.0,
            notes=["Necesitas una rutina activa con días de entrenamiento para medir adherencia."],
        )

    done_by_week: dict[str, int] = defaultdict(int)
    for session in ctx.sessions:
        done_by_week[week_key(session.date)] += 1

    series = [
        {"label": week_label(week), "value": min(round(done / planned * 100), 100)}
        for week, done in sorted(done_by_week.items())
    ]

    average = round(sum(point["value"] for point in series) / len(series)) if series else None

    return MetricResult(
        value=average,
        series=series,
        coverage=1.0,
    )


@metric(
    key="week_streak",
    label="Racha de semanas",
    description=(
        "Semanas naturales seguidas con al menos un entrenamiento. La semana en curso no rompe la "
        "racha mientras no haya terminado: solo cuenta como rota una semana ya cerrada sin ningún "
        "entrenamiento."
    ),
    unit="semanas",
    category=Category.CONSISTENCY,
    scope=Scope.USER,
    chart=Chart.SCALAR,
    higher_is_better=True,
)
def week_streak(ctx: MetricContext) -> MetricResult:
    from ..summary import streak

    resultado = streak(ctx.user, on_date=ctx.today)

    notas = []
    if resultado.this_week_planned:
        notas.append(
            f"Esta semana llevas {resultado.this_week_done} de {resultado.this_week_planned} "
            "entrenamientos planificados."
        )

    return MetricResult(
        value=resultado.weeks,
        notes=notas,
        coverage=1.0,
    )


@metric(
    key="session_density",
    label="Densidad de entrenamiento",
    description=(
        "Kilos movidos por minuto de sesión. Subir la densidad significa hacer el mismo trabajo en "
        "menos tiempo. Solo se calcula con las sesiones en las que quedó registrada la hora de "
        "inicio y de fin."
    ),
    unit="kg/min",
    category=Category.CONSISTENCY,
    scope=Scope.USER,
    chart=Chart.LINE,
    higher_is_better=None,
    requires=(Requires.SESSION_TIMES,),
)
def session_density(ctx: MetricContext) -> MetricResult:
    tonnage_by_session: dict[int, float] = defaultdict(float)
    for set_log in ctx.working_sets:
        load = total_work(set_log, ctx.latest_bodyweight)
        if load is not None and set_log.reps:
            tonnage_by_session[set_log.session_id] += float(load) * set_log.reps

    timed = 0
    series = []
    for session in ctx.sessions:
        if not (session.started_at and session.finished_at):
            continue
        minutes = (session.finished_at - session.started_at).total_seconds() / 60
        if minutes <= 0:
            continue

        timed += 1
        series.append({
            "label": session.date.isoformat(),
            "value": round(tonnage_by_session.get(session.id, 0.0) / minutes, 1),
        })

    values = [point["value"] for point in series]

    return MetricResult(
        value=round(sum(values) / len(values), 1) if values else None,
        series=series,
        coverage=coverage_of(timed, len(ctx.sessions)),
    )
