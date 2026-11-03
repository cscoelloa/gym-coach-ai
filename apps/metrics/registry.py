from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Category(StrEnum):
    STRENGTH = "strength"
    VOLUME = "volume"
    CONSISTENCY = "consistency"
    COMPOSITION = "composition"


CATEGORY_LABELS = {
    Category.STRENGTH: "Fuerza",
    Category.VOLUME: "Volumen",
    Category.CONSISTENCY: "Consistencia",
    Category.COMPOSITION: "Composición corporal",
}


class Scope(StrEnum):
    USER = "user"
    EXERCISE = "exercise"
    MUSCLE = "muscle"


class Chart(StrEnum):
    LINE = "line"
    BAR = "bar"
    TABLE = "table"
    SCALAR = "scalar"


class Requires(StrEnum):
    SESSION_TIMES = "session_times"
    BODYWEIGHT = "bodyweight"
    ROUTINE = "routine"


REQUIRES_LABELS = {
    Requires.SESSION_TIMES: "la hora de inicio y fin de tus sesiones",
    Requires.BODYWEIGHT: "tu peso corporal",
    Requires.ROUTINE: "una rutina activa",
}


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    description: str
    unit: str
    category: Category
    scope: Scope
    chart: Chart
    higher_is_better: bool | None
    requires: tuple[Requires, ...]
    func: Callable[..., "MetricResult"]
    order: int

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS[self.category]


@dataclass
class MetricResult:
    value: float | str | None = None
    series: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    coverage: float = 1.0
    notes: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.value is None and not self.series and not self.rows

    @property
    def coverage_pct(self) -> int:
        return round(self.coverage * 100)


REGISTRY: dict[str, MetricSpec] = {}


def metric(
    *,
    key: str,
    label: str,
    description: str,
    unit: str,
    category: Category,
    scope: Scope = Scope.USER,
    chart: Chart = Chart.SCALAR,
    higher_is_better: bool | None = None,
    requires: tuple[Requires, ...] = (),
):
    def decorator(func: Callable[..., MetricResult]) -> Callable[..., MetricResult]:
        if key in REGISTRY:
            raise ValueError(f"La métrica «{key}» ya está registrada.")
        REGISTRY[key] = MetricSpec(
            key=key,
            label=label,
            description=description,
            unit=unit,
            category=category,
            scope=scope,
            chart=chart,
            higher_is_better=higher_is_better,
            requires=tuple(requires),
            func=func,
            order=len(REGISTRY),
        )
        return func

    return decorator


def get_spec(key: str) -> MetricSpec | None:
    return REGISTRY.get(key)
