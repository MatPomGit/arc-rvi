"""Small validated data types shared across research components."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Viewpoint:
    identifier: str
    x: float
    y: float
    visible_regions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str) or not self.identifier.strip():
            raise ValueError("viewpoint identifier must be a nonempty string")
        if not all(isinstance(v, (int, float)) and isfinite(v) for v in (self.x, self.y)):
            raise ValueError("coordinates must be finite numbers")
        if not self.visible_regions or any(
            not isinstance(region, str) or not region.strip()
            for region in self.visible_regions
        ):
            raise ValueError("visible_regions must contain nonempty names")
        if len(set(self.visible_regions)) != len(self.visible_regions):
            raise ValueError("visible_regions must be unique")


@dataclass(frozen=True)
class InspectionPlan:
    viewpoint_ids: tuple[str, ...]
    covered_regions: tuple[str, ...]
    travel_distance_m: float
