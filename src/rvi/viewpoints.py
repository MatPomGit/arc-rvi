"""Deterministic planar coverage baselines with explicit partial outcomes.

Visibility is supplied by fixtures. No kinematics or collision model is used.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import hypot, isfinite

from .models import InspectionPlan, Viewpoint

METHODS = ("fixed_order", "greedy_coverage", "greedy_distance")


class PlanningError(ValueError):
    """The supplied candidates cannot satisfy the coverage requirements."""


@dataclass(frozen=True)
class PlanningOutcome:
    plan: InspectionPlan
    failure_reason: str | None


def evaluate_viewpoints(
    candidates: Iterable[Viewpoint],
    required_regions: Iterable[str],
    start_xy: tuple[float, float] = (0.0, 0.0),
    *,
    method: str = "greedy_distance",
    max_travel_distance_m: float | None = None,
    budget_selection: str = "feasible_first",
) -> PlanningOutcome:
    """Evaluate a greedy route while retaining evidence before budget exhaustion.

    Historical fixture benchmarks explicitly request legacy_stop; the default
    only ranks candidates currently feasible within the remaining budget.
    Neither variant guarantees an optimal or globally feasible route.
    """
    candidates = tuple(candidates)
    required = tuple(required_regions)
    if not required or any(not isinstance(x, str) or not x.strip() for x in required):
        raise ValueError("required_regions must contain nonempty names")
    if len(set(required)) != len(required):
        raise ValueError("required_regions must be unique")
    if len(start_xy) != 2 or any(
        type(x) not in (float, int) or not isfinite(x) for x in start_xy
    ):
        raise ValueError("start_xy must contain finite coordinates")
    if len({view.identifier for view in candidates}) != len(candidates):
        raise ValueError("duplicate viewpoint identifiers")
    if method not in METHODS:
        raise ValueError("unknown planning method")
    if budget_selection not in ("feasible_first", "legacy_stop"):
        raise ValueError("unknown budget selection policy")
    if max_travel_distance_m is not None and (
        type(max_travel_distance_m) not in (float, int)
        or not isfinite(max_travel_distance_m) or max_travel_distance_m < 0
    ):
        raise ValueError("travel budget must be finite and nonnegative")

    uncovered = set(required)
    position = start_xy
    selected: list[str] = []
    travel = 0.0
    # Fixed shot lists retain input order. Greedy ties use ascending identifiers.
    unused = list(candidates) if method == "fixed_order" else sorted(
        candidates, key=lambda view: view.identifier)
    reason = None
    while uncovered:
        eligible = unused if method == "fixed_order" else [
            view for view in unused if uncovered.intersection(view.visible_regions)]
        if not eligible:
            reason = "unreachable_regions"
            break

        def distance(view):
            return hypot(position[0] - view.x, position[1] - view.y)

        def rank(view):
            gain = len(uncovered.intersection(view.visible_regions))
            if method == "greedy_coverage":
                return (gain,)
            return (gain / (1.0 + distance(view)), gain, -distance(view))

        if (max_travel_distance_m is not None and method != "fixed_order"
                and budget_selection == "feasible_first"):
            feasible = [view for view in eligible
                        if isfinite(distance(view))
                        and travel + distance(view) <= max_travel_distance_m]
            if not feasible:
                reason = "distance_budget_exceeded"
                break
            eligible = feasible
        best = eligible[0] if method == "fixed_order" else max(eligible, key=rank)
        step = distance(best)
        if not isfinite(step) or not isfinite(travel + step):
            raise ValueError("coordinates produce a non-finite route distance")
        # A rejected move acquires no view and consumes no partial travel.
        if max_travel_distance_m is not None and travel + step > max_travel_distance_m:
            reason = "distance_budget_exceeded"
            break
        travel += step
        selected.append(best.identifier)
        uncovered.difference_update(best.visible_regions)
        position = (best.x, best.y)
        unused.remove(best)

    covered = tuple(sorted(set(required) - uncovered))
    return PlanningOutcome(InspectionPlan(tuple(selected), covered, travel), reason)


def plan_viewpoints(
    candidates: Iterable[Viewpoint],
    required_regions: Iterable[str],
    start_xy: tuple[float, float] = (0.0, 0.0),
) -> InspectionPlan:
    """Preserve the original complete-plan API and distance-penalized baseline."""
    required = tuple(required_regions)
    outcome = evaluate_viewpoints(candidates, required, start_xy)
    if outcome.failure_reason:
        missing = sorted(set(required) - set(outcome.plan.covered_regions))
        raise PlanningError(f"uncovered regions: {', '.join(missing)}")
    return outcome.plan
