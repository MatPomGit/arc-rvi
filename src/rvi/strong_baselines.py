"""Strong non-fuzzy baselines for the finite known-geometry model."""

from __future__ import annotations

from copy import copy
from dataclasses import asdict
from math import fsum

from .adapters.simulator import PlanarScene, PlanarSimulator


STRONG_METHODS = (
    "feasible_greedy", "gain_per_cost",
    "receding_horizon_2", "receding_horizon_3",
)


def evaluate_strong_policy(scene: PlanarScene, method: str) -> dict:
    """Execute one decision at a time; never consult the exact evaluator.

    Greedy variants consider positive area gain only. Lookahead searches
    all feasible prefixes up to its horizon, including zero-gain transit
    views, but executes nothing if no prefix adds coverage. Rejected
    predictions do not mutate the real simulation state.
    """
    if method not in STRONG_METHODS:
        raise ValueError("unknown strong baseline")
    sim = PlanarSimulator(scene)
    areas = {p.identifier: p.area_m2 for p in scene.patches}
    required = set(areas)
    total = fsum(areas.values())
    covered: set[str] = set()
    remaining = tuple(range(len(scene.route)))
    events = []
    decisions = []
    expanded = 0
    reason = None

    def area(ids):
        return fsum(areas[k] for k in sorted(ids))

    def successor(state, index):
        nonlocal expanded
        expanded += 1
        nxt = copy(state)
        obs = nxt.acquire(scene.route[index])
        return nxt, obs

    def horizon_choice(depth):
        best_key = None
        best_seq = ()

        def visit(state, current, available, seq):
            nonlocal best_key, best_seq
            if seq and current != covered:
                key = (-area(current), state.elapsed_time_s, len(seq), seq)
                if best_key is None or key < best_key:
                    best_key, best_seq = key, seq
            if len(seq) == depth or current == required:
                return
            for index in available:
                nxt, obs = successor(state, index)
                if obs.failure_reason is None:
                    visit(nxt, current | set(obs.visible_patch_ids),
                          tuple(i for i in available if i != index),
                          seq + (index,))

        visit(sim, covered, remaining, ())
        return best_seq

    def greedy_choice():
        options = []
        for index in remaining:
            nxt, obs = successor(sim, index)
            if obs.failure_reason is not None:
                continue
            gain = area(set(obs.visible_patch_ids) - covered)
            if gain <= 0:
                continue
            cost = nxt.elapsed_time_s - sim.elapsed_time_s
            if method == "feasible_greedy":
                rank = (gain, -cost, -index)
            else:
                # Zero-duration positive gain takes precedence; avoid
                # serializing infinity or dividing by zero.
                rank = (cost == 0, gain / cost if cost else 0,
                        gain, -cost, -index)
            options.append((rank, index))
        return (max(options)[1],) if options else ()

    while covered != required:
        before = expanded
        seq = (horizon_choice(int(method[-1]))
               if method.startswith("receding_horizon") else greedy_choice())
        if not seq:
            reason = "no_feasible_positive_gain_plan"
            decisions.append({"selected": None, "planned_prefix": [],
                              "expanded_transitions": expanded - before})
            break
        index = seq[0]
        identifier = f"view_{index + 1:06d}"
        obs = sim.acquire(scene.route[index])
        if obs.failure_reason is not None:
            raise RuntimeError("accepted prediction disagrees with execution")
        decisions.append({"selected": identifier,
                          "planned_prefix": [i + 1 for i in seq],
                          "expanded_transitions": expanded - before})
        events.append({"candidate_id": identifier,
                       "requested_pose": asdict(scene.route[index]),
                       **asdict(obs)})
        covered.update(obs.visible_patch_ids)
        remaining = tuple(i for i in remaining if i != index)

    return {
        "method": method, "scene_id": scene.identifier,
        "evidence_type": "simulation",
        "status": "completed" if reason is None else "algorithm_failure",
        "failure_reason": reason, "observations": events,
        "covered_patch_ids": sorted(covered),
        "missing_patch_ids": sorted(required - covered),
        "sampled_surface_coverage": area(covered) / total,
        "travel_distance_m": sim.travel_distance_m,
        "elapsed_time_s": sim.elapsed_time_s,
        "expanded_transitions": expanded,
        "decisions": decisions,
    }
