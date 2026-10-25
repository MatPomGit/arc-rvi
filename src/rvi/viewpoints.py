"""Deterministic greedy set-cover baseline with a travel-distance penalty.

This baseline operates on known candidate views and planar distances. It does
not model kinematics, occlusion, collision checking or unknown geometry.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import hypot, isfinite

from .models import InspectionPlan, Viewpoint


class PlanningError(ValueError):
    """The supplied candidates cannot satisfy the coverage requirements."""


def plan_viewpoints(
    candidates: Iterable[Viewpoint],
    required_regions: Iterable[str],
    start_xy: tuple[float, float] = (0.0, 0.0),
) -> InspectionPlan:
    candidates = tuple(candidates)
    required = tuple(required_regions)
    if not required or any(not isinstance(x, str) or not x.strip() for x in required):
        raise ValueError("required_regions must contain nonempty names")
    if len(set(required)) != len(required):
        raise ValueError("required_regions must be unique")
    if len(start_xy) != 2 or any(
        not isinstance(x, (float, int)) or not isfinite(x) for x in start_xy
    ):
        raise ValueError("start_xy must contain finite coordinates")
    if len({view.identifier for view in candidates}) != len(candidates):
        raise ValueError("duplicate viewpoint identifiers")

    uncovered = set(required)
    position = start_xy
    selected: list[str] = []
    travel = 0.0
    unused = sorted(candidates, key=lambda view: view.identifier)

    while uncovered:
        eligible = [view for view in unused if uncovered.intersection(view.visible_regions)]
        if not eligible:
            raise PlanningError(f"uncovered regions: {', '.join(sorted(uncovered))}")

        def rank(view: Viewpoint) -> tuple[float, int, float]:
            gain = len(uncovered.intersection(view.visible_regions))
            distance = hypot(position[0] - view.x, position[1] - view.y)
            return (gain / (1.0 + distance), gain, -distance)

        best = max(eligible, key=rank)
        distance = hypot(position[0] - best.x, position[1] - best.y)
        travel += distance
        selected.append(best.identifier)
        uncovered.difference_update(best.visible_regions)
        position = (best.x, best.y)
        unused.remove(best)

    return InspectionPlan(tuple(selected), tuple(sorted(required)), travel)
