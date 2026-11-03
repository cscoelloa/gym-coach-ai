from dataclasses import dataclass

from .context import DEFAULT_WEEKS, MetricContext
from .models import Metric, UserMetricPreference
from .registry import REGISTRY, REQUIRES_LABELS, MetricResult, MetricSpec, Requires


@dataclass
class ComputedMetric:
    metric: Metric
    spec: MetricSpec
    result: MetricResult

    @property
    def needs(self) -> list[str]:
        if self.result.coverage >= 1:
            return []
        return [REQUIRES_LABELS[Requires(r)] for r in self.spec.requires]

    @property
    def is_reliable(self) -> bool:
        return self.result.coverage >= 0.8

    @property
    def has_no_data(self) -> bool:
        return self.result.is_empty or self.result.coverage == 0

    @property
    def empty_hint(self) -> str:
        if self.result.notes:
            return self.result.notes[0]
        if self.needs:
            return f"Para verlo, registra {' y '.join(self.needs)}."
        return "Todavía no hay datos."


def compute(
    user, *, keys: list[str] | None = None, weeks: int = DEFAULT_WEEKS
) -> list[ComputedMetric]:
    metrics = Metric.objects.filter(is_active=True)
    if keys is not None:
        metrics = metrics.filter(key__in=keys)

    ctx = MetricContext(user=user, weeks=weeks)
    computed = []

    for metric in metrics:
        spec = REGISTRY.get(metric.key)
        if spec is None:
            continue
        computed.append(ComputedMetric(metric=metric, spec=spec, result=spec.func(ctx)))

    return computed


def visible_for(user) -> list[str]:
    preferences = {
        pref.metric.key: pref.is_visible
        for pref in UserMetricPreference.objects.filter(user=user).select_related("metric")
    }

    keys = []
    for metric in Metric.objects.filter(is_active=True):
        wanted = preferences.get(metric.key, metric.default_visible)
        if wanted:
            keys.append(metric.key)
    return keys


def for_ai(user, *, weeks: int = DEFAULT_WEEKS) -> list[ComputedMetric]:
    keys = list(
        Metric.objects.filter(is_active=True, send_to_ai=True).values_list("key", flat=True)
    )
    return compute(user, keys=keys, weeks=weeks)
