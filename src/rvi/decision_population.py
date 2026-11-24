"""Development-only, policy-independent structural P01 population."""

from __future__ import annotations

from collections import Counter
from copy import copy
from dataclasses import asdict, replace
from hashlib import sha256
from itertools import combinations
import json
from math import cos, fsum, pi, radians, remainder, sin
from random import Random

from .adapters.simulator import (
    CameraModel, Circle, MotionModel, PlanarScene, PlanarSimulator,
    SurfacePatch,
)
from .interfaces import CameraPose
from .oracle import exact_oracle


SEED = 20261125
FAMILY_COUNT = 8
CANDIDATE_COUNTS = (6, 8)
FOV_DEG = (18, 55)
BUDGET_RATIOS = (0.8, 1.05, 1.4)
# Every pose is within 3.5 m of the origin; every straight move
# is <=7 m, rotation <=pi/1.5 s, acquisition 0.25 s. Eight
# distinct visits therefore require <100 s if collision-free.
REFERENCE_BUDGET_S = 100.0


def _pose(radius: float, angle: float, yaw: float) -> CameraPose:
    return CameraPose(radius * cos(angle), radius * sin(angle),
                      remainder(yaw, 2 * pi))


def base_scenes():
    """Yield all crossed variants of independent latent radial families.

    Six views are nested in eight; random candidate ordering is fixed
    within each family. No policy or oracle outcome changes generation.
    """
    rng = Random(SEED)
    for i in range(FAMILY_COUNT):
        family = f"decision_dev_{i + 1:03d}"
        phase = rng.uniform(-pi, pi)
        patches = []
        for j in range(6):
            angle = phase + j * pi / 3 + rng.uniform(-.16, .16)
            pose = _pose(rng.uniform(1.15, 1.45), angle, angle)
            patches.append(SurfacePatch(
                f"p{j + 1}", pose.x, pose.y, pose.yaw_rad,
                rng.uniform(.6, 1.4)))
        views = []
        for j in range(8):
            offset = j * pi / 3 if j < 6 else (j - 6 + .5) * pi
            angle = phase + offset + rng.uniform(-.16, .16)
            views.append(_pose(rng.uniform(2.65, 3.35), angle,
                               angle + pi + rng.uniform(-.10, .10)))
        order = list(range(8))
        rng.shuffle(order)
        start = _pose(3.5, phase - .35, phase + pi - .35)
        for n in CANDIDATE_COUNTS:
            for fov in FOV_DEG:
                for obstacle in (False, True):
                    scene_id = f"{family}_n{n}_f{fov}_o{int(obstacle)}"
                    scene = PlanarScene(
                        scene_id, start,
                        CameraModel(radians(fov), .1, 6., radians(75)),
                        MotionModel(1., 1.5, .15, .25, REFERENCE_BUDGET_S),
                        (Circle(0., 0., .85),) if obstacle else (),
                        tuple(patches), tuple(views[j] for j in order if j < n),
                    )
                    yield family, n, fov, obstacle, scene


def structural_features(scene: PlanarScene) -> dict:
    """Measure visibility and feasible direct edges, without any policy."""
    sim = PlanarSimulator(scene)
    required = {p.identifier for p in scene.patches}
    visibility = [set(sim.visible_patches(p)) for p in scene.route]
    pairs = list(combinations(visibility, 2))
    jaccard = [len(a & b) / len(a | b) for a, b in pairs if a | b]
    minimum = next((k for k in range(1, len(visibility) + 1)
                    if any(set().union(*c) == required
                           for c in combinations(visibility, k))), None)
    # The reference budget is deliberately nonbinding. Reuse the simulator
    # rather than approximating collision or rotation cost independently.
    costs = []
    blocked = 0
    n = len(scene.route)
    for i, start in enumerate((scene.start, *scene.route)):
        for j, target in enumerate(scene.route, 1):
            if i == j:
                continue
            state = copy(sim)
            state.pose = start
            observation = state.acquire(target)
            if observation.failure_reason == "path_collision":
                blocked += int(i != 0)
            elif observation.failure_reason is None:
                costs.append(observation.elapsed_time_s)
            else:
                raise ValueError("reference budget unexpectedly binding")
    return {
        "minimum_cover_views_without_motion": minimum,
        "visible_patch_fraction": len(set().union(*visibility)) / len(required),
        "mean_pairwise_jaccard": fsum(jaccard) / len(jaccard) if jaccard else None,
        "nonempty_union_pairs": len(jaccard),
        "blocked_direct_edge_fraction": blocked / (n * (n - 1)) if n > 1 else None,
        "max_accepted_edge_time_s": max(costs, default=None),
        "visible_patch_ids_by_view": [sorted(v) for v in visibility],
    }


def _scene_payload(scene: PlanarScene) -> dict:
    data = asdict(scene)
    data["scene_id"] = data.pop("identifier")
    data["schema_version"] = "1.0.0"
    data["evidence_type"] = "simulation"
    return data


def _hash(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def characterize_base(scene: PlanarScene) -> dict:
    """Cross all budgets; keep even structurally impossible instances."""
    if scene.motion.max_time_s != REFERENCE_BUDGET_S:
        raise ValueError("expected nonbinding reference budget")
    features = structural_features(scene)
    reference = exact_oracle(scene)
    minimum_time = reference["full_min_time_s"]
    budget_reference = (minimum_time if minimum_time is not None else
                        len(scene.route) *
                        (features["max_accepted_edge_time_s"] or 1.0))
    if budget_reference <= 0:
        raise ValueError("nonpositive budget reference")
    cases = []
    for ratio in BUDGET_RATIOS:
        case = replace(
            scene, identifier=f"{scene.identifier}_r{round(ratio * 100):03d}",
            motion=replace(scene.motion, max_time_s=budget_reference * ratio),
        )
        result = exact_oracle(case)
        sim = PlanarSimulator(case)
        immediate = [j for j, pose in enumerate(case.route, 1)
                     if copy(sim).acquire(pose).failure_reason is None]
        full_first = [j for j, t in enumerate(
            result["first_full_min_times_s"], 1) if t is not None]
        if not set(full_first) <= set(immediate):
            raise ValueError("inconsistent first-action feasibility")
        if bool(full_first) != result["full_feasible"]:
            raise ValueError("inconsistent full-route witness")
        dead_end = (len(immediate) - len(full_first)) / len(immediate) if full_first else None
        payload = _scene_payload(case)
        cases.append({
            "scene": payload, "scene_sha256": _hash(payload),
            "budget_ratio": ratio,
            "budget_reference_type": "minimum_full_time" if minimum_time is not None
            else "fallback_max_edge_times_candidate_count",
            "budget_reference_s": budget_reference,
            "immediately_feasible_first_views": immediate,
            "completion_feasible_first_views": full_first,
            "first_action_dead_end_fraction": dead_end,
            "oracle": result,
        })
    return {"scene_id": scene.identifier, "features": features,
            "reference_oracle": reference, "cases": cases}


def _summarize(rows: list[dict]) -> dict:
    cases = [c for row in rows for c in row["cases"]]
    feasible = [c for c in cases if c["oracle"]["full_feasible"]]
    sensitive = [c for c in feasible if c["first_action_dead_end_fraction"] > 0]
    return {
        "base_scenes": len(rows), "instances": len(cases),
        "structurally_feasible_base_scenes": sum(
            row["reference_oracle"]["full_feasible"] for row in rows),
        "budget_feasible_instances": len(feasible),
        "budget_infeasible_instances": len(cases) - len(feasible),
        "order_sensitive_feasible_instances": len(sensitive),
        "order_sensitive_fraction": len(sensitive) / len(feasible) if feasible else None,
        "minimum_cover_views_histogram": dict(Counter(
            str(row["features"]["minimum_cover_views_without_motion"])
            for row in rows)),
    }


def generate_decision_population() -> dict:
    """Generate all structural strata before comparing any policy."""
    rows = []
    for family, n, fov, obstacle, scene in base_scenes():
        rows.append(dict(characterize_base(scene), family=family,
                         candidate_count=n, fov_deg=fov,
                         central_obstacle=obstacle))
    if len(rows) != FAMILY_COUNT * len(CANDIDATE_COUNTS) * len(FOV_DEG) * 2:
        raise ValueError("incomplete structural population")
    summary = _summarize(rows)
    return {
        "schema_version": "1.0.0", "study_id": "01",
        "evidence_type": "simulation", "stage": "exploratory_not_confirmatory",
        "partition": "development_decision", "independent_unit": "geometry_family",
        "design": "radial_decision_structure_v1", "seed": SEED,
        "family_count": FAMILY_COUNT, "selection": "none_retain_all",
        "policy_evaluations": 0, "reference_budget_s": REFERENCE_BUDGET_S,
        "scene_hash_encoding": "sorted compact UTF-8 JSON",
        "summary": summary,
        "by_family": {f: _summarize([r for r in rows if r["family"] == f])
                      for f in sorted({r["family"] for r in rows})},
        "by_candidate_count": {str(n): _summarize(
            [r for r in rows if r["candidate_count"] == n])
            for n in CANDIDATE_COUNTS},
        "by_fov_deg": {str(f): _summarize(
            [r for r in rows if r["fov_deg"] == f]) for f in FOV_DEG},
        "by_obstacle": {str(o).lower(): _summarize(
            [r for r in rows if r["central_obstacle"] == o])
            for o in (False, True)},
        "by_budget_ratio": {str(b): _summarize([
            dict(r, cases=[c for c in r["cases"] if c["budget_ratio"] == b])
            for r in rows]) for b in BUDGET_RATIOS},
        "rows": rows,
    }
