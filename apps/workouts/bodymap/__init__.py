from dataclasses import dataclass

from ..taxonomy import REGION_INERT, muscle_for_region, muscle_label
from .paths import REGIONS

VIEWBOX_FRONT = "0 0 35 93"
VIEWBOX_BACK = "37 0 35 93"


@dataclass(frozen=True)
class Region:
    id: str
    muscle: str | None
    label: str
    d: str

    @property
    def is_inert(self) -> bool:
        return self.muscle is None


def _build(view: str) -> tuple[Region, ...]:
    return tuple(
        Region(
            id=region_id,
            muscle=muscle_for_region(region_id),
            label=(
                muscle_label(muscle_for_region(region_id))
                if muscle_for_region(region_id)
                else original
            ),
            d=d,
        )
        for region_id, original, region_view, d in REGIONS
        if region_view == view
    )


def _ordered(view: str) -> tuple[Region, ...]:
    regiones = _build(view)
    return tuple(r for r in regiones if r.is_inert) + tuple(r for r in regiones if not r.is_inert)


FRONT = _ordered("front")
BACK = _ordered("back")

PAINTED_MUSCLES = tuple(
    dict.fromkeys(r.muscle for r in FRONT + BACK if r.muscle is not None)
)


@dataclass(frozen=True)
class PaintedRegion:
    id: str
    muscle: str | None
    label: str
    d: str
    level: int
    is_active: bool
    css: str
    url: str

    @property
    def is_inert(self) -> bool:
        return self.muscle is None


@dataclass(frozen=True)
class PaintedView:
    name: str
    caption: str
    viewbox: str
    regions: tuple[PaintedRegion, ...]


def painted(
    levels: dict[str, int] | None = None,
    active: str | None = None,
    urls: dict[str, str] | None = None,
) -> list[PaintedView]:
    levels = levels or {}
    urls = urls or {}

    def resolver(region: Region) -> PaintedRegion:
        nivel = 0 if region.muscle is None else int(levels.get(region.muscle, 0))
        activo = region.muscle is not None and region.muscle == active
        return PaintedRegion(
            id=region.id,
            muscle=region.muscle,
            label=region.label,
            d=region.d,
            level=nivel,
            is_active=activo,
            css="bm-inert" if region.muscle is None else ("bm-on" if activo else f"bm-{nivel}"),
            url="" if region.muscle is None else urls.get(region.muscle, ""),
        )

    return [
        PaintedView("front", "Frente", VIEWBOX_FRONT, tuple(resolver(r) for r in FRONT)),
        PaintedView("back", "Espalda", VIEWBOX_BACK, tuple(resolver(r) for r in BACK)),
    ]


__all__ = [
    "BACK",
    "FRONT",
    "PAINTED_MUSCLES",
    "REGION_INERT",
    "VIEWBOX_BACK",
    "VIEWBOX_FRONT",
    "PaintedRegion",
    "PaintedView",
    "Region",
    "painted",
]
