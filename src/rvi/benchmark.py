"""Paired inspection evaluation, deterministic records and software provenance."""

from __future__ import annotations

from dataclasses import asdict
import json
from math import fsum, hypot
from pathlib import Path

from .adapters.simulator import PlanarScene, PlanarSimulator, exact_fields, load_scene
from .evidence import digest, software_provenance
from .scenarios import load_scenario, name, number, read_json
from .viewpoints import METHODS, evaluate_viewpoints


def run_benchmark(suite_path: Path) -> dict:
    """Evaluate every method on a paired fixture or geometric simulation suite."""
    suite, raw = read_json(suite_path)
    if suite.get("evidence_type") == "simulation":
        return _simulation_suite(suite_path, suite, raw)
    required = {"schema_version", "suite_id", "evidence_type", "scenarios",
                "max_travel_distance_m"}
    if suite.keys() != required:
        raise ValueError("suite needs schema_version, suite_id, evidence_type, scenarios and max_travel_distance_m")
    if suite["schema_version"] != "1.0.0" or suite["evidence_type"] != "fixture":
        raise ValueError("only version 1.0.0 fixture suites are supported")
    suite_id = name(suite["suite_id"], "suite_id")
    budget = number(suite["max_travel_distance_m"], "max_travel_distance_m", nonnegative=True)
    entries = suite["scenarios"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("scenarios must be a nonempty list of relative JSON paths")

    scenarios = []
    seen_ids = set()
    seen_paths = set()
    for entry in entries:
        name(entry, "scenario path")
        relative = Path(entry)
        if relative.is_absolute():
            raise ValueError("scenario paths must be relative to the suite")
        path = (suite_path.parent / relative).resolve(strict=True)
        scenario, scenario_raw = load_scenario(path)
        if path in seen_paths or scenario.identifier in seen_ids:
            raise ValueError("duplicate scenario file or scenario_id")
        seen_paths.add(path)
        seen_ids.add(scenario.identifier)
        scenarios.append((scenario, {"path": entry, "scenario_id": scenario.identifier,
                                    "sha256": digest(scenario_raw)}))

    source = software_provenance()
    inputs = {"suite_sha256": digest(raw), "scenarios": [item for _, item in scenarios]}
    # This identifies an evaluation specification, not an independent replication.
    run_id = digest(json.dumps({"inputs": inputs, "source": source}, sort_keys=True).encode())
    trials = []
    for scenario, manifest in scenarios:
        for method in METHODS:
            outcome = evaluate_viewpoints(scenario.viewpoints, scenario.required_regions,
                                          scenario.start_xy, method=method,
                                          max_travel_distance_m=budget)
            plan = outcome.plan
            trials.append({
                "trial_id": f"{len(trials) + 1:06d}", "run_id": run_id,
                "scenario_id": scenario.identifier, "scenario_sha256": manifest["sha256"],
                "method": method, "evidence_type": "fixture",
                "status": "completed" if outcome.failure_reason is None else "algorithm_failure",
                "failure_reason": outcome.failure_reason,
                "viewpoint_ids": list(plan.viewpoint_ids),
                "covered_regions": list(plan.covered_regions),
                "missing_regions": sorted(set(scenario.required_regions) - set(plan.covered_regions)),
                "coverage_fraction": len(plan.covered_regions) / len(scenario.required_regions),
                "travel_distance_m": plan.travel_distance_m,
            })
    summary = []
    for method in METHODS:
        rows = [trial for trial in trials if trial["method"] == method]
        count = len(rows)
        failures = {}
        for row in rows:
            if row["failure_reason"] is not None:
                reason = row["failure_reason"]
                failures[reason] = failures.get(reason, 0) + 1
        successes = sum(row["status"] == "completed" for row in rows)
        summary.append({"method": method, "trial_count": count,
                        "success_count": successes, "success_fraction": successes / count,
                        "mean_coverage_fraction": fsum(row["coverage_fraction"] / count for row in rows),
                        "mean_travel_distance_m": fsum(row["travel_distance_m"] / count for row in rows),
                        "failures": failures})
    return {"schema_version": "1.0.0", "run_id": run_id, "study_id": "01",
            "suite_id": suite_id, "evidence_type": "fixture",
            "randomness": "none", "source": source, "inputs": inputs,
            "max_travel_distance_m": budget, "methods": list(METHODS),
            "trials": trials, "summary": summary}


def evaluate_simulation_policy(scene: PlanarScene, method: str) -> dict:
    """Compare known-geometry policies; score only observations actually acquired."""
    if method not in METHODS:
        raise ValueError("unknown planning method")
    simulator = PlanarSimulator(scene)
    candidates = [(f"view_{index:06d}", pose, set(simulator.visible_patches(pose)))
                  for index, pose in enumerate(scene.route, start=1)]
    required = {patch.identifier for patch in scene.patches}
    covered = set()
    events = []
    reason = None
    while covered != required:
        eligible = candidates if method == "fixed_order" else [
            entry for entry in candidates if entry[2] - covered]
        if not eligible:
            reason = "unreachable_regions"
            break

        def rank(entry):
            gain = len(entry[2] - covered)
            distance = hypot(entry[1].x - simulator.pose.x, entry[1].y - simulator.pose.y)
            return (gain,) if method == "greedy_coverage" else (gain / (1 + distance), gain, -distance)

        # Stable candidate IDs preserve the same tie rule and pairing across methods.
        chosen = eligible[0] if method == "fixed_order" else max(eligible, key=rank)
        identifier, pose, _ = chosen
        observation = simulator.acquire(pose)
        events.append({"candidate_id": identifier, "requested_pose": asdict(pose),
                       **asdict(observation)})
        covered.update(observation.visible_patch_ids)
        candidates.remove(chosen)
        if observation.failure_reason:
            reason = observation.failure_reason
            break
    total = fsum(patch.area_m2 for patch in scene.patches)
    area = fsum(patch.area_m2 for patch in scene.patches if patch.identifier in covered)
    return {"method": method, "scene_id": scene.identifier, "evidence_type": "simulation",
            "status": "completed" if reason is None else "algorithm_failure",
            "failure_reason": reason, "observations": events,
            "covered_patch_ids": sorted(covered), "missing_patch_ids": sorted(required - covered),
            "sampled_surface_coverage": area / total,
            "travel_distance_m": simulator.travel_distance_m,
            "elapsed_time_s": simulator.elapsed_time_s}


def _simulation_suite(path: Path, suite: dict, raw: bytes) -> dict:
    exact_fields(suite, {"schema_version", "suite_id", "evidence_type", "scenes"}, "simulation suite")
    if suite["schema_version"] != "1.0.0":
        raise ValueError("only version 1.0.0 simulation suites are supported")
    suite_id = name(suite["suite_id"], "suite_id")
    if not isinstance(suite["scenes"], list) or not suite["scenes"]:
        raise ValueError("scenes must be a nonempty list of relative paths")
    trials, manifests = [], []
    seen_paths, seen_ids = set(), set()
    for entry in suite["scenes"]:
        relative = Path(name(entry, "scene path"))
        if relative.is_absolute():
            raise ValueError("scene paths must be relative to the suite")
        scene_path = (path.parent / relative).resolve(strict=True)
        scene, scene_raw = load_scene(scene_path)
        if scene_path in seen_paths or scene.identifier in seen_ids:
            raise ValueError("duplicate scene file or scene_id")
        seen_paths.add(scene_path)
        seen_ids.add(scene.identifier)
        scene_hash = digest(scene_raw)
        manifests.append({"path": entry, "scene_id": scene.identifier, "sha256": scene_hash})
        for method in METHODS:
            trial = evaluate_simulation_policy(scene, method)
            trial.update(trial_id=f"{len(trials) + 1:06d}", scene_sha256=scene_hash)
            trials.append(trial)
    summary = []
    for method in METHODS:
        rows = [row for row in trials if row["method"] == method]
        count = len(rows)
        reasons = {}
        for row in rows:
            if row["failure_reason"] is not None:
                reason = row["failure_reason"]
                reasons[reason] = reasons.get(reason, 0) + 1
        summary.append({"method": method, "trial_count": count,
                        "success_count": sum(row["status"] == "completed" for row in rows),
                        "mean_sampled_surface_coverage": fsum(row["sampled_surface_coverage"] / count for row in rows),
                        "mean_elapsed_time_s": fsum(row["elapsed_time_s"] / count for row in rows),
                        "mean_travel_distance_m": fsum(row["travel_distance_m"] / count for row in rows),
                        "failures": reasons})
    return {"schema_version": "1.0.0", "suite_id": suite_id, "study_id": "01",
            "evidence_type": "simulation", "model": "planar_geometry_kinematics_v1",
            "visibility_access": "known_geometry_oracle", "randomness": "none",
            "source": software_provenance(), "suite_sha256": digest(raw),
            "scenes": manifests, "methods": list(METHODS), "trials": trials, "summary": summary}
