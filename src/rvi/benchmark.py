"""Paired inspection evaluation, deterministic records and software provenance."""

from __future__ import annotations

from dataclasses import asdict
import json
from math import atan2, cos, fsum, hypot, sin
from pathlib import Path

from .adapters.simulator import PlanarScene, PlanarSimulator, exact_fields, load_scene
from .geometry import angular_distance
from .interfaces import CameraPose
from .perception import SensorConfig, load_sensor_config, simulate_sensor
from .evidence import digest, software_provenance
from .scenarios import load_scenario, name, number, read_json
from .viewpoints import METHODS, evaluate_viewpoints

SENSOR_METHODS = ("fixed_order", "nearest_pose", "sensor_parallax")


def run_benchmark(suite_path: Path, sensor_path: Path | None = None) -> dict:
    """Evaluate every method on a paired fixture or geometric simulation suite."""
    suite, raw = read_json(suite_path)
    if suite.get("evidence_type") == "simulation":
        if sensor_path is not None:
            sensor, sensor_raw = load_sensor_config(sensor_path)
            return _simulation_suite(suite_path, suite, raw, sensor,
                                     digest(sensor_raw))
        return _simulation_suite(suite_path, suite, raw)
    if sensor_path is not None:
        raise ValueError("sensor observations require a simulation suite")
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



def select_observation_view(
    candidates: list[tuple[str, CameraPose]],
    current: CameraPose,
    history: list[tuple[CameraPose, dict]],
    method: str,
    horizontal_fov_rad: float,
) -> tuple[str, CameraPose]:
    """Choose using only candidate poses and previously acquired sensor features."""
    if method not in SENSOR_METHODS or not candidates:
        raise ValueError("unknown method or empty candidate views")
    if method == "fixed_order":
        return candidates[0]

    def distance(item: tuple[str, CameraPose]) -> float:
        return hypot(item[1].x - current.x, item[1].y - current.y)

    if method == "nearest_pose":
        return min(candidates, key=distance)

    estimated = []
    for pose, observation in history:
        if observation["status"] != "captured":
            continue
        for feature in observation["detections"]:
            # One-dimensional pinhole bearing plus measured range in metres.
            bearing = (0.5 - feature["u_px"] / observation["width_px"])
            bearing = pose.yaw_rad + bearing * horizontal_fov_rad
            range_m = feature["range_m"]
            if range_m <= 0:
                continue
            px = pose.x + range_m * cos(bearing)
            py = pose.y + range_m * sin(bearing)
            estimated.append((px, py, pose.x, pose.y))
    if not estimated:
        return min(candidates, key=distance)

    def rank(item: tuple[str, CameraPose]) -> tuple[float, float]:
        _, candidate = item
        differences = []
        for px, py, ox, oy in estimated:
            if (px, py) == (candidate.x, candidate.y):
                continue
            observed_bearing = atan2(py - oy, px - ox)
            new_bearing = atan2(py - candidate.y, px - candidate.x)
            differences.append(angular_distance(new_bearing, observed_bearing))
        # A documented angular-baseline heuristic, NOT a calibrated uncertainty.
        novelty = fsum(differences) / len(differences) if differences else 0
        return novelty, -distance(item)

    return max(candidates, key=rank)


def evaluate_observation_policy(
    scene: PlanarScene,
    sensor: SensorConfig,
    method: str,
) -> dict:
    """Route from past observations; independently score sensor-detected patches."""
    if method not in SENSOR_METHODS:
        raise ValueError("unknown sensor-based policy")
    simulator = PlanarSimulator(scene)
    candidates = [(f"view_{index:06d}", pose)
                  for index, pose in enumerate(scene.route, 1)]
    candidate_indices = {identifier: index for index, (identifier, _) in
                         enumerate(candidates, 1)}
    history: list[tuple[CameraPose, dict]] = []
    events, reference_events = [], []
    detected = set()
    failure = None
    while candidates:
        identifier, pose = select_observation_view(
            candidates, simulator.pose, history, method,
            scene.camera.horizontal_fov_rad)
        candidates.remove((identifier, pose))
        motion = simulator.acquire(pose)
        event = {
            "candidate_id": identifier,
            "requested_pose": asdict(pose),
            "actual_pose": asdict(motion.pose),
            "elapsed_time_s": motion.elapsed_time_s,
            "travel_distance_m": motion.travel_distance_m,
            "failure_reason": motion.failure_reason,
            "policy_observation": None,
        }
        if motion.failure_reason is not None:
            failure = motion.failure_reason
            events.append(event)
            break
        policy, evaluator = simulate_sensor(
            scene, motion.pose, sensor, capture_index=candidate_indices[identifier],
            timestamp_s=motion.elapsed_time_s)
        event["policy_observation"] = policy
        events.append(event)
        history.append((motion.pose, policy))
        reference_events.append({
            "candidate_id": identifier,
            "geometry_references": evaluator["geometry_references"],
        })
        detected.update(
            row["patch_id"] for row in evaluator["geometry_references"]
            if row["detected"]
        )

    total_area = fsum(patch.area_m2 for patch in scene.patches)
    acquired_area = fsum(patch.area_m2 for patch in scene.patches
                         if patch.identifier in detected)
    return {
        "method": method, "scene_id": scene.identifier,
        "evidence_type": "simulation",
        "model": "planar_sensor_observation_v1",
        "visibility_access": "observations_only",
        "status": "completed" if failure is None else "algorithm_failure",
        "failure_reason": failure,
        "observations": events,
        "evaluator": {
            "detected_patch_ids": sorted(detected),
            "missed_patch_ids": sorted(p.identifier for p in scene.patches
                                     if p.identifier not in detected),
            "steps": reference_events,
        },
        "sampled_surface_coverage": acquired_area / total_area,
        "coverage_complete": len(detected) == len(scene.patches),
        "travel_distance_m": simulator.travel_distance_m,
        "elapsed_time_s": simulator.elapsed_time_s,
    }


def _simulation_suite(path: Path, suite: dict, raw: bytes,
                      sensor: SensorConfig | None = None,
                      sensor_sha256: str | None = None) -> dict:
    exact_fields(suite, {"schema_version", "suite_id", "evidence_type", "scenes"}, "simulation suite")
    if suite["schema_version"] != "1.0.0":
        raise ValueError("only version 1.0.0 simulation suites are supported")
    suite_id = name(suite["suite_id"], "suite_id")
    if sensor is not None and ("holdout" in suite_id.lower()
                               or "confirm" in suite_id.lower()):
        raise ValueError("observation-only exploratory mode refuses held-out suites")
    if not isinstance(suite["scenes"], list) or not suite["scenes"]:
        raise ValueError("scenes must be a nonempty list of relative paths")
    trials, manifests = [], []
    methods = SENSOR_METHODS if sensor is not None else METHODS
    seen_paths, seen_ids = set(), set()
    for entry in suite["scenes"]:
        relative = Path(name(entry, "scene path"))
        if relative.is_absolute():
            raise ValueError("scene paths must be relative to the suite")
        if sensor is not None and any(
                "holdout" in part.lower() or "confirm" in part.lower()
                for part in relative.parts):
            raise ValueError("observation-only exploratory mode refuses held-out paths")
        scene_path = (path.parent / relative).resolve(strict=True)
        scene, scene_raw = load_scene(scene_path)
        if scene_path in seen_paths or scene.identifier in seen_ids:
            raise ValueError("duplicate scene file or scene_id")
        seen_paths.add(scene_path)
        seen_ids.add(scene.identifier)
        scene_hash = digest(scene_raw)
        manifests.append({"path": entry, "scene_id": scene.identifier, "sha256": scene_hash})
        for method in methods:
            trial = (evaluate_simulation_policy(scene, method) if sensor is None
                     else evaluate_observation_policy(scene, sensor, method))
            trial.update(trial_id=f"{len(trials) + 1:06d}", scene_sha256=scene_hash)
            trials.append(trial)
    summary = []
    for method in methods:
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
    result = {
        "schema_version": "1.0.0", "suite_id": suite_id, "study_id": "01",
        "evidence_type": "simulation",
        "model": ("planar_geometry_kinematics_v1" if sensor is None
                  else "planar_sensor_observation_v1"),
        "visibility_access": ("known_geometry_oracle" if sensor is None
                              else "observations_only"),
        "randomness": "none" if sensor is None else "seeded_per_candidate",
        "source": software_provenance(), "suite_sha256": digest(raw),
        "scenes": manifests, "methods": list(methods),
        "trials": trials, "summary": summary,
    }
    if sensor is not None:
        result.update(
            stage="exploratory_not_confirmatory",
            sensor_sha256=sensor_sha256,
            observation_boundary="policy_input_separate_from_evaluator",
            sampling_unit="hand_constructed_scene_not_independent_population",
        )
    return result
