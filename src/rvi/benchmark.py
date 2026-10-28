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
        record = {"method": method, "trial_count": count,
                  "success_count": sum(row["status"] == "completed" for row in rows),
                  "mean_sampled_surface_coverage": fsum(row["sampled_surface_coverage"] / count for row in rows),
                  "mean_elapsed_time_s": fsum(row["elapsed_time_s"] / count for row in rows),
                  "mean_travel_distance_m": fsum(row["travel_distance_m"] / count for row in rows),
                  "failures": reasons}
        if sensor is not None:
            # Executing the candidate route is not proof of full observed coverage.
            record["execution_complete_count"] = record["success_count"]
            record["coverage_complete_count"] = sum(trial["coverage_complete"] for trial in rows)
            record["coverage_complete_fraction"] = record["coverage_complete_count"] / count
        summary.append(record)
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
