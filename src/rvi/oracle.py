"""Bounded exact evaluator for deterministic known-geometry pilot scenes."""

from __future__ import annotations

from collections import Counter
from copy import copy
from math import fsum, isclose, isfinite

from .adapters.simulator import PlanarScene, PlanarSimulator


MAX_CANDIDATES = 9


def exact_oracle(scene: PlanarScene) -> dict:
    """Enumerate all feasible prefixes of distinct candidate indices.

    Use the same acquisition transition as the evaluated policies. Zero-gain
    transit views are allowed. No continuous path search, return constraint,
    revisits, hidden perception or physical feasibility is inferred.
    """
    if len(scene.route) > MAX_CANDIDATES:
        raise ValueError("exact oracle candidate limit exceeded")
    areas = {patch.identifier: patch.area_m2 for patch in scene.patches}
    required = set(areas)
    simulator = PlanarSimulator(scene)
    total_area = fsum(areas.values())
    best = (0.0, 0.0, ())
    full = None
    first_times = [None] * len(scene.route)
    prefixes = 0

    def visit(state, covered, used, route):
        nonlocal best, full, prefixes
        prefixes += 1
        coverage = fsum(areas[k] for k in sorted(covered)) / total_area
        key = (-coverage, state.elapsed_time_s, route)
        if key < best:
            best = key
        if covered == required:
            key = (state.elapsed_time_s, route)
            if full is None or key < full:
                full = key
            index = route[0] - 1
            if first_times[index] is None or key[0] < first_times[index]:
                first_times[index] = key[0]
            return
        for index, pose in enumerate(scene.route):
            if index in used:
                continue
            successor = copy(state)
            observation = successor.acquire(pose)
            if observation.failure_reason is None:
                visit(successor, covered | set(observation.visible_patch_ids),
                      used | {index}, route + (index + 1,))

    # best stores negative coverage for lexicographic minimization.
    visit(simulator, set(), set(), ())
    return {
        "full_feasible": full is not None,
        "optimal_coverage": -best[0],
        "optimal_elapsed_s": best[1],
        "optimal_route": list(best[2]),
        "full_min_time_s": None if full is None else full[0],
        "full_route": None if full is None else list(full[1]),
        "first_full_min_times_s": first_times,
        "prefixes": prefixes,
    }


def diagnose_trials(scene: PlanarScene, trials: list[dict]) -> dict:
    """Compare each completed or failed policy with the exact evaluator."""
    result = exact_oracle(scene)
    areas = {p.identifier: p.area_m2 for p in scene.patches}
    required = set(areas)
    total = fsum(areas.values())
    rows = []
    methods = set()
    for trial in trials:
        method = trial["method"]
        if method in methods or trial["scene_id"] != scene.identifier:
            raise ValueError("duplicate method or mismatched oracle scene")
        methods.add(method)
        status = trial["status"]
        if status not in ("completed", "algorithm_failure"):
            raise ValueError("unsupported oracle trial status")
        success = status == "completed"
        ids = trial["covered_patch_ids"]
        covered = set(ids)
        missing = trial["missing_patch_ids"]
        coverage = trial["sampled_surface_coverage"]
        if (len(covered) != len(ids) or not covered <= required
                or len(set(missing)) != len(missing)
                or set(missing) != required - covered
                or success != (covered == required)
                or success != (trial["failure_reason"] is None)
                or not isfinite(coverage) or not 0 <= coverage <= 1
                or not isclose(coverage, fsum(areas[k] for k in covered) / total,
                               rel_tol=0, abs_tol=1e-12)):
            raise ValueError("inconsistent policy coverage or status")
        gap = result["optimal_coverage"] - coverage
        if ((success and not result["full_feasible"])
                or (gap < 0 and not isclose(gap, 0, abs_tol=1e-12))):
            raise ValueError("policy outcome exceeds exact oracle")
        classification = ("success" if success else
                          "avoidable" if result["full_feasible"] else
                          "infeasible")
        rows.append({"method": method, "classification": classification,
                     "coverage_gap": max(0.0, gap),
                     "failure_reason": trial["failure_reason"]})
    return {"scene_id": scene.identifier, **result, "methods": rows}


def summarize_oracle(cases: list[dict]) -> dict:
    """Descriptive instance and method counts; no independent-trial inference."""
    if not cases:
        raise ValueError("empty oracle population")
    methods = {row["method"] for row in cases[0]["methods"]}
    if not methods or any(
        len(case["methods"]) != len(methods)
        or {row["method"] for row in case["methods"]} != methods
        for case in cases
    ):
        raise ValueError("incomplete oracle method matrix")

    def summarize(rows):
        counts = Counter(row["classification"] for row in rows)
        feasible = counts["success"] + counts["avoidable"]
        failures = counts["avoidable"] + counts["infeasible"]
        return {"trials": len(rows), "success": counts["success"],
                "avoidable": counts["avoidable"],
                "infeasible": counts["infeasible"],
                "failures": failures, "feasible": feasible,
                "mean_coverage_gap": fsum(row["coverage_gap"] for row in rows)
                / len(rows),
                "avoidable_failure_rate": counts["avoidable"] / feasible
                if feasible else None,
                "avoidable_share_of_failures": counts["avoidable"] / failures
                if failures else None}

    rows = [row for case in cases for row in case["methods"]]
    return {"instances": len(cases),
            "feasible_instances": sum(c["full_feasible"] for c in cases),
            "all": summarize(rows),
            "methods": {method: summarize([row for row in rows
                                           if row["method"] == method])
                        for method in sorted(methods)}}
