"""Audit the serialized development population before publishing evidence."""

import json
import sys
from hashlib import sha256
from math import fsum, isclose
from pathlib import Path
from tempfile import TemporaryDirectory

from rvi.adapters.simulator import PlanarSimulator, load_scene
from rvi.decision_population import BUDGET_RATIOS, _summarize, base_scenes
from rvi.oracle import exact_oracle


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay(scene, route):
    sim = PlanarSimulator(scene)
    covered = set()
    require(len(route) == len(set(route)), "duplicate route index")
    for index in route:
        require(type(index) is int and 1 <= index <= len(scene.route),
                "invalid route index")
        event = sim.acquire(scene.route[index - 1])
        require(event.failure_reason is None, "infeasible route witness")
        covered.update(event.visible_patch_ids)
    return covered, sim.elapsed_time_s


def verify(report):
    expected = {s.identifier: (f, n, v, o, s)
                for f, n, v, o, s in base_scenes()}
    rows = report["rows"]
    require(len(rows) == len(expected), "base count mismatch")
    seen = set()
    with TemporaryDirectory() as directory:
        path = Path(directory) / "scene.json"
        for row in rows:
            identifier = row["scene_id"]
            require(identifier in expected and identifier not in seen,
                    "unexpected or duplicate base scene")
            seen.add(identifier)
            family, n, fov, obstacle, base = expected[identifier]
            require((row["family"], row["candidate_count"], row["fov_deg"],
                     row["central_obstacle"]) == (family, n, fov, obstacle),
                    "factor mismatch")
            reference = exact_oracle(base)
            require(row["reference_oracle"] == reference,
                    "reference oracle mismatch")
            require([c["budget_ratio"] for c in row["cases"]]
                    == list(BUDGET_RATIOS), "budget grid mismatch")
            for case in row["cases"]:
                payload = case["scene"]
                raw = json.dumps(payload, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False)
                require(sha256(raw.encode("utf-8")).hexdigest()
                        == case["scene_sha256"], "scene hash mismatch")
                path.write_text(raw, encoding="utf-8")
                scene, _ = load_scene(path)
                require(scene.identifier == (
                    f"{identifier}_r{round(case['budget_ratio'] * 100):03d}"),
                    "case identifier mismatch")
                require((scene.start, scene.camera, scene.obstacles,
                         scene.patches, scene.route) ==
                        (base.start, base.camera, base.obstacles,
                         base.patches, base.route), "case geometry mismatch")
                require(isclose(scene.motion.max_time_s,
                                case["budget_reference_s"] * case["budget_ratio"],
                                rel_tol=0, abs_tol=1e-12), "budget mismatch")
                result = case["oracle"]
                require(result == exact_oracle(scene), "oracle result mismatch")
                covered, elapsed = replay(scene, result["optimal_route"])
                areas = {p.identifier: p.area_m2 for p in scene.patches}
                require(isclose(fsum(areas[k] for k in covered) /
                                fsum(areas.values()), result["optimal_coverage"],
                                abs_tol=1e-12), "coverage witness mismatch")
                require(isclose(elapsed, result["optimal_elapsed_s"],
                                abs_tol=1e-12), "elapsed witness mismatch")
                immediate = [i for i, pose in enumerate(scene.route, 1)
                             if PlanarSimulator(scene).acquire(pose).failure_reason
                             is None]
                first = [i for i, t in enumerate(
                    result["first_full_min_times_s"], 1) if t is not None]
                require(immediate == case["immediately_feasible_first_views"]
                        and first == case["completion_feasible_first_views"]
                        and set(first) <= set(immediate)
                        and bool(first) == result["full_feasible"],
                        "first-action feasibility mismatch")
                fraction = (len(immediate) - len(first)) / len(immediate) if first else None
                require(fraction == case["first_action_dead_end_fraction"],
                        "dead-end fraction mismatch")
                if result["full_feasible"]:
                    covered, elapsed = replay(scene, result["full_route"])
                    require(covered == set(areas) and isclose(
                        elapsed, result["full_min_time_s"], abs_tol=1e-12),
                        "full-route witness mismatch")
    require(report["summary"] == _summarize(rows), "summary mismatch")
    for key, field in (("by_family", "family"),
                       ("by_candidate_count", "candidate_count"),
                       ("by_fov_deg", "fov_deg"),
                       ("by_obstacle", "central_obstacle")):
        groups = {}
        for row in rows:
            value = str(row[field]).lower() if field == "central_obstacle" else str(row[field])
            groups.setdefault(value, []).append(row)
        require(report[key] == {k: _summarize(v) for k, v in groups.items()},
                f"{key} mismatch")
    require(report["by_budget_ratio"] == {
        str(b): _summarize([dict(r, cases=[c for c in r["cases"]
                                          if c["budget_ratio"] == b])
                            for r in rows]) for b in BUDGET_RATIOS},
        "budget summary mismatch")


if __name__ == "__main__":
    verify(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print("PASS: decision population integrity")
