"""Exploratory paired pilot analysis with family-level uncertainty."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random

from .benchmark import run_benchmark
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


def _check_hash(root: Path, record: dict) -> Path:
    if not isinstance(record, dict) or not isinstance(record.get("sha256"), str):
        raise ValueError("invalid manifest hash record")
    path = _file(root, record.get("path"))
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
