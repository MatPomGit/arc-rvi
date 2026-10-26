"""Paired fixture evaluation, deterministic records and software provenance."""

from __future__ import annotations

import json
from math import fsum
from pathlib import Path

from .evidence import digest, software_provenance
from .scenarios import load_scenario, name, number, read_json
from .viewpoints import METHODS, evaluate_viewpoints


def run_benchmark(suite_path: Path) -> dict:
    """Evaluate every method on every declared fixture, with no random resampling."""
    suite, raw = read_json(suite_path)
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
