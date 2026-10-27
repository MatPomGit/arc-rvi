"""Offline, replayable benchmark batches with explicit evidence boundaries.

This is a software-level study01 adapter, not a general physical experiment
executor. Holdout scenarios and external robot I/O are intentionally forbidden.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path

from .benchmark import run_benchmark
from .evidence import software_provenance
from .pilot import _check_hash
from .scenarios import read_json
from .viewpoints import METHODS

VERSION = "1.0.0"
ALLOWED_PARTITIONS = ("development", "pilot")
SPLITS = ("development", "pilot", "holdout")
CONDITIONS = ("nominal", "occluded")


def _encode(data: dict | list) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("invalid relative input path")
    if any(part in ("", ".", "..") for part in relative.replace("\\", "/").split("/")):
        raise ValueError("input path must not contain traversal components")
    candidate = root / relative
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root.resolve(strict=True)) or not resolved.is_file():
        raise ValueError("input path leaves its manifest root")
    if candidate.is_symlink():
        raise ValueError("symlinked input files are not permitted")
    return resolved


def _validate_manifest(manifest_path: Path, partition: str) -> tuple[dict, dict, Path, str]:
    if partition not in ALLOWED_PARTITIONS:
        raise ValueError("holdout and confirmation partitions are not exposed to batch")
    manifest_path = Path(manifest_path)
    manifest, raw = read_json(manifest_path)
    if (manifest.get("schema_version"), manifest.get("study_id"),
            manifest.get("evidence_type"), manifest.get("stage"),
            manifest.get("visibility_access")) != (
            VERSION, "01", "simulation", "exploratory_not_confirmatory",
            "known_geometry_oracle"):
        raise ValueError("batch only accepts exploratory study01 simulation manifests")
    partitions, suites, rows = (manifest.get(key) for key in
                                ("partitions", "suites", "scenes"))
    if not isinstance(partitions, dict) or set(partitions) != set(SPLITS):
        raise ValueError("invalid partition mapping")
    if not isinstance(suites, dict) or set(suites) != set(SPLITS):
        raise ValueError("missing partition suite records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("missing scene records")
    family_groups = {}
    seen_scenes, seen_paths, pairs = set(), set(), {}
    for split in SPLITS:
        families = partitions[split]
        if not isinstance(families, list) or not families or any(
                not isinstance(v, str) or not v for v in families):
            raise ValueError("invalid geometry family assignment")
        if len(set(families)) != len(families):
            raise ValueError("duplicate geometry family")
        for family in families:
            if family in family_groups:
                raise ValueError("geometry family leaked between partitions")
            family_groups[family] = split
    selected = []
    for row in rows:
        if not isinstance(row, dict) or not {"scene_id", "partition", "family",
               "pair_id", "replicate", "condition", "paired_seed", "sha256",
               "path"} <= row.keys():
            raise ValueError("invalid scene manifest record")
        split, family = row["partition"], row["family"]
        if split not in SPLITS or family_groups.get(family) != split:
            raise ValueError("scene family inconsistent with partitions")
        if (not isinstance(row["scene_id"], str) or not row["scene_id"]
                or not isinstance(row["pair_id"], str) or not row["pair_id"]):
            raise ValueError("invalid scene or pair identity")
        if row["condition"] not in CONDITIONS or type(row["replicate"]) is not int or row["replicate"] < 0:
            raise ValueError("invalid paired scenario condition or replicate")
        if type(row["paired_seed"]) is not int or not 0 <= row["paired_seed"] < 2**64:
            raise ValueError("invalid paired seed")
        if not isinstance(row["sha256"], str) or len(row["sha256"]) != 64:
            raise ValueError("invalid SHA-256 scene record")
        if not isinstance(row["path"], str) or not row["path"].startswith("scenes/" + split + "/"):
            raise ValueError("scene path partition mismatch")
        if row["scene_id"] in seen_scenes or row["path"] in seen_paths:
            raise ValueError("duplicate scene ID or path")
        seen_scenes.add(row["scene_id"])
        seen_paths.add(row["path"])
        pair = (split, row["pair_id"])
        other = pairs.setdefault(pair, {})
        if row["condition"] in other:
            raise ValueError("duplicate paired condition")
        if any(old["family"] != family or old["replicate"] != row["replicate"]
               or old["paired_seed"] != row["paired_seed"] for old in other.values()):
            raise ValueError("mismatched pairing metadata")
        other[row["condition"]] = row
        if split == partition:
            selected.append(row)
    if any(set(pair) != set(CONDITIONS) for pair in pairs.values()):
        raise ValueError("incomplete paired conditions")
    if not selected:
        raise ValueError("empty selected partition")
    root = manifest_path.resolve(strict=True).parent
    suite_record = suites[partition]
    if not isinstance(suite_record, dict) or set(suite_record) != {"path", "sha256"}:
        raise ValueError("invalid suite record")
    if suite_record["path"] != f"suites/{partition}.json":
        raise ValueError("suite path does not match partition")
    # Only selected-partition suite and scene bytes are opened.
    suite_path = _check_hash(root, suite_record)
    suite, _ = read_json(suite_path)
    if (suite.get("suite_id"), suite.get("evidence_type")) != (
            f"study01_{partition}", "simulation"):
        raise ValueError("incompatible partition suite")
    entries = suite.get("scenes")
    if not isinstance(entries, list) or len(entries) != len(selected):
        raise ValueError("suite has incomplete or extra scene entries")
    expected = {"../" + row["path"] for row in selected}
    if set(entries) != expected or len(set(entries)) != len(entries):
        raise ValueError("suite scene listing disagrees with manifest")
    for row in selected:
        _check_hash(root, row)
    return manifest, {row["scene_id"]: row for row in selected}, suite_path, _sha(raw)


def _validate_report(report: dict, selected: dict, evidence: str) -> None:
    if report.get("evidence_type") != evidence or set(report.get("methods", [])) != set(METHODS):
        raise ValueError("benchmark output has wrong evidence type or incomplete methods")
    trials = report.get("trials")
    if not isinstance(trials, list) or len(trials) != len(selected) * len(METHODS):
        raise ValueError("benchmark output has an incomplete trial matrix")
    observed = set()
    for trial in trials:
        key = (trial.get("scene_id") if evidence == "simulation"
               else trial.get("scenario_id"), trial.get("method"))
        if key in observed or key[0] not in selected or key[1] not in METHODS:
            raise ValueError("duplicate or unexpected trial")
        observed.add(key)
        meta = selected[key[0]]
        if trial.get("scene_sha256" if evidence == "simulation" else "scenario_sha256") != meta["sha256"]:
            raise ValueError("trial source SHA-256 mismatch")
        status, reason = trial.get("status"), trial.get("failure_reason")
        if status not in ("completed", "algorithm_failure") or (
                status == "completed" and reason is not None) or (
                status == "algorithm_failure" and (not isinstance(reason, str) or not reason)):
            raise ValueError("inconsistent trial terminal status")
        for metric in ("travel_distance_m", "sampled_surface_coverage" if evidence == "simulation"
                       else "coverage_fraction"):
            value = trial.get(metric)
            if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid numerical benchmark result")
    if len(observed) != len(selected) * len(METHODS):
        raise ValueError("missing trial method pairs")


def _fixture_suite(path: Path) -> tuple[dict, dict, str]:
    path = Path(path)
    suite, raw = read_json(path)
    if suite.get("evidence_type") != "fixture":
        raise ValueError("direct suite mode is fixture-only; simulation needs a split manifest")
    if suite.get("schema_version") != VERSION:
        raise ValueError("unsupported fixture suite")
    report = run_benchmark(path)
    selected = {}
    for row in report.get("inputs", {}).get("scenarios", []):
        if row["scenario_id"] in selected:
            raise ValueError("duplicate fixture scenario")
        selected[row["scenario_id"]] = {"sha256": row["sha256"], "condition": "fixture",
                                       "family": row["scenario_id"], "pair_id": row["scenario_id"],
                                       "replicate": 0, "paired_seed": None}
    return report, selected, _sha(raw)


def _payload(manifest: Path | None, suite: Path | None, partition: str) -> tuple[dict, dict, dict]:
    if (manifest is None) == (suite is None):
        raise ValueError("choose exactly one manifest or fixture suite")
    if manifest is not None:
        metadata, selected, suite_path, input_sha = _validate_manifest(manifest, partition)
        report = run_benchmark(suite_path)
        if report.get("suite_sha256") != metadata["suites"][partition]["sha256"]:
            raise ValueError("suite source hash changed during benchmark")
        evidence, input_kind = "simulation", "partition_manifest"
    else:
        if partition != "pilot":
            raise ValueError("fixture suite mode does not accept a partition selector")
        report, selected, input_sha = _fixture_suite(suite)
        evidence, input_kind = "fixture", "fixture_suite"
    _validate_report(report, selected, evidence)
    source = report["source"]
    run_id = _sha(_encode({"input_sha256": input_sha, "partition": partition,
                           "source_sha256": source["package_source_sha256"],
                           "suite_sha256": report.get("suite_sha256"), "evidence": evidence}))
    records = []
    for trial in report["trials"]:
        identifier = trial["scene_id"] if evidence == "simulation" else trial["scenario_id"]
        meta = selected[identifier]
        seeds = {
            "geometry": meta["paired_seed"],
            "sensor": None,
            "method": None,
            "analysis": None,
        }
        records.append({
            "run_id": run_id, "trial_id": f"{run_id[:12]}-{trial['trial_id']}",
            "study_id": "01", "independent_unit": meta["family"],
            "scenario_id": identifier, "pair_id": meta["pair_id"],
            "replicate_id": meta["replicate"], "condition": meta["condition"],
            "method": trial["method"], "evidence_type": evidence,
            "status": trial["status"], "failure_reason": trial["failure_reason"],
            "seeds": seeds, "input_sha256": meta["sha256"],
            "primary_metric": {
                "name": "sampled_surface_coverage" if evidence == "simulation" else "coverage_fraction",
                "value": trial["sampled_surface_coverage" if evidence == "simulation" else "coverage_fraction"],
                "unit": "fraction",
            },
            "secondary": {
                "travel_distance_m": trial["travel_distance_m"],
                "elapsed_model_time_s": trial.get("elapsed_time_s"),
            },
            "attempts": trial.get("observations", []),
        })
    totals = Counter(r["status"] for r in records)
    summary = {
        "schema_version": VERSION, "run_id": run_id, "study_id": "01",
        "partition": partition if evidence == "simulation" else "fixture_smoke",
        "evidence_type": evidence, "status": "exploratory_not_confirmatory",
        "independent_unit": "geometry_family" if evidence == "simulation" else "fixture_scenario",
        "families": len({r["independent_unit"] for r in records}),
        "scenarios": len(selected), "methods": list(METHODS),
        "trials": len(records), "statuses": dict(sorted(totals.items())),
        "baseline_summary": report["summary"],
        "model": report.get("model"),
        "visibility_access": report.get("visibility_access"),
    }
    provenance = {
        "schema_version": VERSION, "run_id": run_id, "study_id": "01",
        "protocol_version": "unfrozen", "partition": summary["partition"],
        "evidence_type": evidence, "source": source, "input_kind": input_kind,
        "input_sha256": input_sha,
        "benchmark_output_sha256": _sha(_encode(report)),
        "suite_sha256": report.get("suite_sha256") or report["inputs"]["suite_sha256"],
        "visibility_access": report.get("visibility_access"),
        "seed_domains": ["geometry", "sensor", "method", "analysis"],
        "uncertified_future_domains": ["sensor", "method", "analysis"],
    }
    return {"trials.json": _encode(records), "summary.json": _encode(summary)}, provenance, report


def run_experiment(*, manifest: Path | None = None, suite: Path | None = None,
                   partition: str = "pilot", output_dir: Path, resume: bool = False) -> dict:
    """Write immutable deterministic outputs; resume verifies and never rewrites."""
    output_dir = Path(output_dir)
    # Validate/replay before inspecting a stored receipt: changing input or code
    # makes a mismatched resume fail without touching previous evidence.
    started = datetime.now(timezone.utc).isoformat()
    payloads, provenance, _ = _payload(manifest, suite, partition)
    hashes = {filename: {"sha256": _sha(raw), "size_bytes": len(raw)}
              for filename, raw in payloads.items()}
    if output_dir.exists() or output_dir.is_symlink():
        if not resume or output_dir.is_symlink() or not output_dir.is_dir():
            raise ValueError("output directory already exists; use --resume to verify")
        receipt_path = output_dir / "receipt.json"
        if receipt_path.is_symlink():
            raise ValueError("symlinked receipt is forbidden")
        receipt, _ = read_json(receipt_path)
        if receipt.get("provenance") != provenance or receipt.get("artifacts") != hashes:
            raise ValueError("existing receipt disagrees with current input or source")
        if {p.name for p in output_dir.iterdir()} != {*payloads, "receipt.json"}:
            raise ValueError("extra or missing files in experiment directory")
        for filename, expected in hashes.items():
            path = output_dir / filename
            if path.is_symlink() or not path.is_file() or _sha(path.read_bytes()) != expected["sha256"]:
                raise ValueError("existing experiment artifact was modified or corrupted")
        return receipt
    receipt = {
        "schema_version": VERSION, "provenance": provenance, "artifacts": hashes,
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "wall_clock_times": "execution_receipt_only; deterministic artifact content omits wall clock",
    }
    payloads["receipt.json"] = _encode(receipt)
    created = False
    try:
        output_dir.mkdir(parents=True, exist_ok=False)
        created = True
        for filename, raw in payloads.items():
            with (output_dir / filename).open("xb") as file:
                file.write(raw)
    except BaseException:
        if created:
            for filename in payloads:
                (output_dir / filename).unlink(missing_ok=True)
            try:
                output_dir.rmdir()
            except OSError:
                pass
        raise
    return receipt
