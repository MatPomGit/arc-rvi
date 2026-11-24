"""Exploratory paired pilot analysis with family-level uncertainty."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random

from .benchmark import FUZZY_METHODS, run_benchmark
from .viewpoints import METHODS

CONDITIONS = ("nominal", "occluded")
MIN_BOOTSTRAP_FAMILIES = 8


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("manifest contains an invalid relative path")
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("manifest path escapes the generated directory")
    return path


def _check_hash(root: Path, record: dict, *, directory: Path | None = None) -> Path:
    if not isinstance(record, dict) or not isinstance(record.get("sha256"), str):
        raise ValueError("invalid manifest hash record")
    path = _file(root, record.get("path"))
    if directory is not None and not path.is_relative_to(directory):
        raise ValueError("manifest path outside pilot directory")
    if _sha(path.read_bytes()) != record["sha256"]:
        raise ValueError("manifest SHA-256 mismatch")
    return path


def _strict_pairs(entries: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in entries:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_manifest(path: Path) -> tuple[dict, Path, str]:
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_pairs,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid manifest JSON") from exc
    if not isinstance(manifest, dict) or (manifest.get("study_id"), manifest.get("evidence_type"),
                                         manifest.get("stage"), manifest.get("visibility_access")) != (
            "01", "simulation", "exploratory_not_confirmatory", "known_geometry_oracle"):
        raise ValueError("manifest is not an exploratory study01 simulation")
    root = path.resolve().parent
    suites, scenes = manifest.get("suites"), manifest.get("scenes")
    if not isinstance(suites, dict) or set(suites) != {"development", "pilot", "holdout"}:
        raise ValueError("manifest partitions are incomplete")
    if not isinstance(scenes, list) or not scenes or any(not isinstance(row, dict) for row in scenes):
        raise ValueError("manifest scenes are missing or malformed")
    pilot_records = [row for row in scenes if row.get("partition") == "pilot"]
    if not pilot_records:
        raise ValueError("manifest does not include pilot scenes")
    # Holdout scene files are not accessed during pilot analysis.
    for record in pilot_records:
        _check_hash(root, record)
    return manifest, _check_hash(root, suites["pilot"]), _sha(raw)


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"invalid {label}")
    return float(value)


def _percentiles(values: list[float]) -> list[float]:
    ordered = sorted(values)
    def at(q: float) -> float:
        x = q * (len(ordered) - 1)
        lo = int(x)
        return ordered[lo] + (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]) * (x - lo)
    return [at(0.025), at(0.975)]


def _intervals(effects: list[dict], seed: int, draws: int) -> dict:
    if len(effects) < MIN_BOOTSTRAP_FAMILIES:
        return {"status": "descriptive_only", "reason": "fewer_than_eight_independent_families",
                "confidence_intervals": None}
    rng = random.Random(seed)
    completion, coverage = [], []
    for _ in range(draws):
        sample = [effects[rng.randrange(len(effects))] for _ in effects]
        completion.append(math.fsum(row["completion_loss_difference"] for row in sample) / len(sample))
        coverage.append(math.fsum(row["coverage_loss_difference"] for row in sample) / len(sample))
    return {"status": "exploratory_cluster_bootstrap", "method": "family_resampling_percentile",
            "draws": draws, "seed": seed, "confidence_level": 0.95,
            "confidence_intervals": {"completion_loss_difference": _percentiles(completion),
                                     "coverage_loss_difference": _percentiles(coverage)}}


def summarize_pilot(manifest: dict, report: dict, reference: str, comparator: str,
                    *, seed: int = 20261026, draws: int = 10000) -> dict:
    """Validate a complete paired report before calculating descriptive effects."""
    if reference == comparator or reference not in METHODS or comparator not in METHODS:
        raise ValueError("choose two different registered benchmark methods")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**64:
        raise ValueError("analysis seed must be a nonnegative 64-bit integer")
    if isinstance(draws, bool) or not isinstance(draws, int) or not 100 <= draws <= 100000:
        raise ValueError("bootstrap draws must be between 100 and 100000")
    if (report.get("evidence_type"), report.get("visibility_access"), report.get("model")) != (
            "simulation", "known_geometry_oracle", "planar_geometry_kinematics_v1"):
        raise ValueError("report has an incompatible model or evidence type")
    if report.get("suite_id") != "study01_pilot" or set(report.get("methods", [])) != set(METHODS):
        raise ValueError("wrong pilot suite or incomplete benchmark methods")
    declared = [row for row in manifest["scenes"] if row["partition"] == "pilot"]
    if len(declared) == 0 or len({row["scene_id"] for row in declared}) != len(declared):
        raise ValueError("missing or duplicate pilot scene records")
    scenes = {row["scene_id"]: row for row in declared}
    hashes = {row["scene_id"]: row["sha256"] for row in declared}
    if len(report.get("scenes", [])) != len(scenes) or {
            row["scene_id"]: row["sha256"] for row in report["scenes"]} != hashes:
        raise ValueError("report scene hashes disagree with pilot manifest")
    groups = defaultdict(dict)
    families = {}
    for row in declared:
        if row["condition"] not in CONDITIONS or not row.get("family") or not row.get("pair_id"):
            raise ValueError("invalid pairing metadata")
        key = row["pair_id"]
        if key in families and families[key] != row["family"]:
            raise ValueError("pair spans different geometry families")
        families[key] = row["family"]
        if row["condition"] in groups[key]:
            raise ValueError("duplicate pair condition")
        groups[key][row["condition"]] = row["scene_id"]
    if any(set(pair) != set(CONDITIONS) for pair in groups.values()):
        raise ValueError("incomplete nominal/occluded pair")
    trials = report.get("trials")
    if not isinstance(trials, list) or len(trials) != len(scenes) * len(METHODS):
        raise ValueError("missing or extra benchmark trials")
    observed = {}
    failure_counts = defaultdict(Counter)
    for row in trials:
        key = (row.get("scene_id"), row.get("method"))
        if key in observed or key[0] not in scenes or key[1] not in METHODS:
            raise ValueError("duplicate or unexpected benchmark trial")
        if row.get("scene_sha256") != hashes[key[0]] or row.get("evidence_type") != "simulation":
            raise ValueError("trial provenance mismatch")
        coverage = _number(row.get("sampled_surface_coverage"), "coverage")
        elapsed = _number(row.get("elapsed_time_s"), "elapsed time")
        distance = _number(row.get("travel_distance_m"), "travel distance")
        if not 0 <= coverage <= 1 or elapsed < 0 or distance < 0:
            raise ValueError("trial metric out of range")
        status, reason = row.get("status"), row.get("failure_reason")
        if (status == "completed" and (reason is not None or not math.isclose(coverage, 1.0, abs_tol=1e-8))) or (
                status == "algorithm_failure" and (not isinstance(reason, str) or not reason)) or status not in (
                "completed", "algorithm_failure"):
            raise ValueError("inconsistent completion and failure")
        observed[key] = {"completion": int(status == "completed"), "coverage": coverage,
                         "elapsed_time_s": elapsed, "travel_distance_m": distance}
        if reason is not None:
            failure_counts[(key[1], scenes[key[0]]["condition"])][reason] += 1
    if len(observed) != len(scenes) * len(METHODS):
        raise ValueError("incomplete paired method matrix")

    family_pairs = defaultdict(list)
    for pair_id, conditions in groups.items():
        contrast = {}
        for method in (reference, comparator):
            n, o = (observed[(conditions[condition], method)] for condition in CONDITIONS)
            contrast[method] = {metric: n[metric] - o[metric] for metric in ("completion", "coverage")}
        family_pairs[families[pair_id]].append({
            "pair_id": pair_id,
            "completion_loss_difference": contrast[comparator]["completion"] - contrast[reference]["completion"],
            "coverage_loss_difference": contrast[comparator]["coverage"] - contrast[reference]["coverage"],
        })
    effects = []
    for family, rows in sorted(family_pairs.items()):
        effects.append({"family": family, "pair_count": len(rows),
                        **{name: math.fsum(row[name] for row in rows) / len(rows)
                           for name in ("completion_loss_difference", "coverage_loss_difference")}})
    stats = []
    for method in METHODS:
        for condition in CONDITIONS:
            rows = [observed[(scene_id, method)] for scene_id, meta in scenes.items()
                    if meta["condition"] == condition]
            stats.append({"method": method, "condition": condition, "trials": len(rows),
                          "completed": sum(row["completion"] for row in rows),
                          "mean_model_coverage": math.fsum(row["coverage"] for row in rows) / len(rows),
                          "mean_model_elapsed_time_s": math.fsum(row["elapsed_time_s"] for row in rows) / len(rows),
                          "failures": dict(sorted(failure_counts[(method, condition)].items()))})
    return {"schema_version": "1.0.0", "study_id": "01", "partition": "pilot",
            "stage": "exploratory_not_confirmatory", "evidence_type": "simulation",
            "completion_definition": "all_reference_patches_acquired_in_planar_model",
            "visibility_access": "known_geometry_oracle", "reference": reference, "comparator": comparator,
            "effect_direction": "comparator_nominal_minus_occluded_loss_minus_reference_loss",
            "independent_unit": "geometry_family", "families": len(effects), "pairs": len(groups),
            "method_condition": stats, "family_effects": effects,
            "estimated_effects": {name: math.fsum(row[name] for row in effects) / len(effects)
                                  for name in ("completion_loss_difference", "coverage_loss_difference")},
            "uncertainty": _intervals(effects, seed, draws)}


def analyze_pilot(manifest_path: Path, reference: str = "fixed_order",
                  comparator: str = "greedy_distance", *, seed: int = 20261026) -> dict:
    manifest, suite, manifest_sha = _read_manifest(manifest_path)
    report = run_benchmark(suite)
    if report.get("suite_sha256") != manifest["suites"]["pilot"]["sha256"]:
        raise ValueError("report suite hash does not match manifest")
    summary = summarize_pilot(manifest, report, reference, comparator, seed=seed)
    summary["provenance"] = {
        "manifest_sha256": manifest_sha,
        "suite_sha256": report["suite_sha256"],
        "benchmark_report_sha256": _sha(json.dumps(report, sort_keys=True,
                                                allow_nan=False).encode("utf-8")),
        "source": report["source"],
    }
    return summary


FACTORIAL_CELLS = tuple(
    f"o_{occlusion}__i_reference__c_{clutter}"
    for occlusion in ("none", "moderate", "strong")
    for clutter in ("none", "dense")
)
FACTORIAL_METHODS = METHODS + FUZZY_METHODS


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON: {value}")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        _reject_constant(value)
    return result


def analyze_factorial_pilot(manifest_path: Path) -> dict:
    """Run only the reference-brightness pilot and retain all benchmark reports."""
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw, object_pairs_hook=_strict_pairs,
                          parse_constant=_reject_constant, parse_float=_finite_float)
    if not isinstance(manifest, dict):
        raise ValueError("invalid factorial manifest")
    if (manifest.get("design"), manifest.get("study_id"),
            manifest.get("stage"), manifest.get("evidence_type")) != (
            "sampled_factorial_v1", "01", "exploratory_not_confirmatory",
            "simulation"):
        raise ValueError("expected exploratory study01 factorial manifest")
    root = manifest_path.resolve().parent
    partitions = manifest["partitions"]
    if (not isinstance(partitions, dict)
            or set(partitions) != {"development", "pilot", "holdout"}
            or any(not isinstance(split, list) or not split
                   or any(not isinstance(f, str) or not f.strip() for f in split)
                   for split in partitions.values())):
        raise ValueError("invalid partitions")
    families = partitions["pilot"]
    all_families = [f for split in partitions.values() for f in split]
    if not families or len(set(all_families)) != len(all_families):
        raise ValueError("duplicate or missing partition families")
    repeats = manifest["replicates_per_family"]
    if type(repeats) is not int or not 1 <= repeats <= 4:
        raise ValueError("invalid replicate count")
    expected = {(f, r, c) for f in families for r in range(repeats)
                for c in FACTORIAL_CELLS}
    records = {}
    ids = set()
    if not isinstance(manifest.get("scenes"), list):
        raise ValueError("invalid factorial scenes")
    for row in manifest["scenes"]:
        if (not isinstance(row, dict)
                or any(not isinstance(row.get(field), str) or not row[field].strip()
                       for field in ("family", "scene_id", "pair_id", "cell_id", "partition"))
                or type(row.get("replicate")) is not int):
            raise ValueError("invalid factorial scene identifiers")
        if row["partition"] != "pilot":
            if row["family"] in families:
                raise ValueError("pilot family appears outside pilot partition")
            continue
        if row["cell_id"] not in FACTORIAL_CELLS:
            continue
        key = (row["family"], row["replicate"], row["cell_id"])
        if key not in expected or key in records or row["scene_id"] in ids:
            raise ValueError("duplicate or unexpected factorial scene")
        expected_factors = dict(zip(
            ("occlusion", "illumination", "clutter"),
            (row["cell_id"].split("__")[0][2:], "reference",
             row["cell_id"].split("__")[2][2:])))
        if row["factors"] != expected_factors:
            raise ValueError("factor metadata mismatch")
        _check_hash(root, row, directory=root / "scenes" / "pilot")
        records[key] = row
        ids.add(row["scene_id"])
    if set(records) != expected:
        raise ValueError("incomplete factorial scene matrix")
    for f in families:
        for r in range(repeats):
            block = [records[f, r, c] for c in FACTORIAL_CELLS]
            for field in ("pair_id", "paired_seed", "geometry_patch_count"):
                if len({row[field] for row in block}) != 1:
                    raise ValueError("inconsistent paired scene metadata")
    reports = {}
    observed = {}
    for cell in FACTORIAL_CELLS:
        suite_record = manifest["suites"]["pilot"][cell]
        suite = _check_hash(root, suite_record, directory=root / "suites" / "pilot")
        # Validate suite membership before running any policy.
        declared = {row["scene_id"]: row for key, row in records.items()
                    if key[2] == cell}
        suite_data = json.loads(suite.read_bytes(), object_pairs_hook=_strict_pairs,
                                parse_constant=_reject_constant, parse_float=_finite_float)
        paths = [(suite.parent / entry).resolve() for entry in suite_data["scenes"]]
        expected_paths = {_file(root, row["path"]) for row in declared.values()}
        if len(paths) != len(expected_paths) or set(paths) != expected_paths:
            raise ValueError("suite membership differs from pilot manifest")
        report = run_benchmark(suite, fuzzy_pilot=True)
        if (report["suite_sha256"] != suite_record["sha256"]
                or report["visibility_access"] != "known_geometry_oracle"
                or report["stage"] != "exploratory_not_confirmatory"
                or tuple(report["methods"]) != FACTORIAL_METHODS):
            raise ValueError("incompatible factorial benchmark report")
        if len(report["scenes"]) != len(declared) or {
            row["scene_id"]: row["sha256"] for row in report["scenes"]
        } != {k: v["sha256"] for k, v in declared.items()}:
            raise ValueError("report scene provenance mismatch")
        for row in report["trials"]:
            meta = declared.get(row["scene_id"])
            if meta is None or row["scene_sha256"] != meta["sha256"]:
                raise ValueError("trial provenance mismatch")
            key = (meta["family"], meta["replicate"], cell, row["method"])
            if key in observed or row["method"] not in FACTORIAL_METHODS:
                raise ValueError("duplicate or unexpected factorial trial")
            coverage = _number(row["sampled_surface_coverage"], "coverage")
            elapsed = _number(row["elapsed_time_s"], "elapsed")
            distance = _number(row["travel_distance_m"], "distance")
            status, reason = row["status"], row["failure_reason"]
            if not 0 <= coverage <= 1 or min(elapsed, distance) < 0:
                raise ValueError("invalid factorial trial metrics")
            if not ((status == "completed" and reason is None
                     and math.isclose(coverage, 1.0, abs_tol=1e-8))
                    or (status == "algorithm_failure"
                        and isinstance(reason, str) and reason)):
                raise ValueError("invalid factorial trial outcome")
            observed[key] = row
        reports[cell] = report
    if set(observed) != {(*key, m) for key in expected
                         for m in FACTORIAL_METHODS}:
        raise ValueError("incomplete factorial trial matrix")

    def mean(values):
        values = list(values)
        return math.fsum(values) / len(values)

    method_cells = []
    family_results = []
    for method in FACTORIAL_METHODS:
        for cell in FACTORIAL_CELLS:
            rows = [observed[f, r, cell, method] for f in families
                    for r in range(repeats)]
            method_cells.append({
                "method": method, "cell": cell, "trials": len(rows),
                "success_fraction": mean(row["status"] == "completed" for row in rows),
                "mean_coverage": mean(row["sampled_surface_coverage"] for row in rows),
                "mean_elapsed_time_s": mean(row["elapsed_time_s"] for row in rows),
                "mean_distance_m": mean(row["travel_distance_m"] for row in rows),
                "failures": dict(Counter(row["failure_reason"] for row in rows
                                         if row["failure_reason"] is not None)),
            })
        for f in families:
            successes = [mean(observed[f, r, cell, method]["status"] == "completed"
                              for r in range(repeats)) for cell in FACTORIAL_CELLS]
            challenge = mean(successes[1:])
            family_results.append({"family": f, "method": method,
                                   "nominal_success": successes[0],
                                   "challenge_success": challenge,
                                   "loss": successes[0] - challenge})
    by_key = {(row["family"], row["method"]): row for row in family_results}
    contrasts = []
    for reference in FACTORIAL_METHODS:
        if reference == "fuzzy_budget":
            continue
        effects = [by_key[f, reference]["loss"] - by_key[f, "fuzzy_budget"]["loss"]
                   for f in families]
        contrasts.append({"reference": reference, "candidate": "fuzzy_budget",
                          "mean_loss_difference": mean(effects),
                          "family_effects": dict(zip(families, effects))})
    return {"schema_version": "1.0.0", "study_id": "01",
            "stage": "exploratory_not_confirmatory", "partition": "pilot",
            "evidence_type": "simulation", "visibility_access": "known_geometry_oracle",
            "independent_unit": "geometry_family", "families": len(families),
            "trial_count": len(observed), "illumination": "reference_only",
            "effect_direction": "reference_loss_minus_candidate_loss",
            "uncertainty": "descriptive_only",
            "method_cells": method_cells, "family_results": family_results,
            "contrasts": contrasts, "manifest_sha256": _sha(raw),
            "reports": reports}
