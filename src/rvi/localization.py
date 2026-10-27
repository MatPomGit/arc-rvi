"""Deterministic instance assignment on supplied fixture distances only.

No image features, camera pose, sensor fusion or physical localization is
computed here. Ground truth is passed only to the separate evaluator.
"""
from __future__ import annotations

import json
from math import isfinite
from pathlib import Path

from .evidence import sha256_file, software_provenance

METHODS = ("visual", "spatial", "fused")
VERSION = "1.0.0"


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _nonfinite(value: str):
    raise ValueError(f"non-finite JSON constant: {value}")


def _fields(value: object, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"invalid {label} fields")
    return value


def _id(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _fraction(value: object, label: str) -> float:
    if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    return float(value)


def select_instance(
    candidates: list[dict], method: str, threshold: float, ambiguity_margin: float
) -> dict:
    """Select a candidate by supplied normalized distances, or abstain.

    This function never receives ground-truth identities or evaluator metadata.
    """
    if method not in METHODS:
        raise ValueError("unknown localization method")
    threshold = _fraction(threshold, "threshold")
    ambiguity_margin = _fraction(ambiguity_margin, "ambiguity margin")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    seen: set[str] = set()
    ranked: list[tuple[float, str]] = []
    for candidate in candidates:
        _fields(candidate, {"id", "visual_distance", "spatial_distance"}, "candidate")
        identifier = _id(candidate["id"], "candidate id")
        if identifier in seen:
            raise ValueError("duplicate candidate id")
        seen.add(identifier)
        visual = _fraction(candidate["visual_distance"], "visual distance")
        spatial = _fraction(candidate["spatial_distance"], "spatial distance")
        score = {"visual": visual, "spatial": spatial,
                 "fused": (visual + spatial) / 2}[method]
        ranked.append((score, identifier))
    ranked.sort()
    if not ranked:
        return {"selected_id": None, "score": None, "decision": "no_candidate"}
    best, identifier = ranked[0]
    if best > threshold:
        return {"selected_id": None, "score": best, "decision": "threshold_rejection"}
    if len(ranked) > 1 and ranked[1][0] - best <= ambiguity_margin:
        return {"selected_id": None, "score": best, "decision": "ambiguous"}
    return {"selected_id": identifier, "score": best, "decision": "selected"}


def _outcome(selected: str | None, truth: str | None) -> str:
    if selected is None:
        return "correct_rejection" if truth is None else "abstained"
    return "correct_selection" if selected == truth else "wrong_selection"


def run_localization_fixture(path: Path) -> dict:
    """Evaluate three baselines on the same requests without data leakage."""
    path = Path(path)
    suite = json.loads(path.read_bytes().decode("utf-8"),
                       object_pairs_hook=_pairs, parse_constant=_nonfinite)
    _fields(suite, {"schema_version", "evidence_type", "suite_id",
                    "threshold", "ambiguity_margin", "requests"}, "suite")
    if suite["schema_version"] != VERSION or suite["evidence_type"] != "fixture":
        raise ValueError("unsupported localization fixture schema or evidence type")
    suite_id = _id(suite["suite_id"], "suite id")
    threshold = _fraction(suite["threshold"], "threshold")
    margin = _fraction(suite["ambiguity_margin"], "ambiguity margin")
    requests = suite["requests"]
    if not isinstance(requests, list) or not requests:
        raise ValueError("requests must be a nonempty list")
    trials: list[dict] = []
    used: set[str] = set()
    for request in requests:
        _fields(request, {"request_id", "ground_truth_id", "candidates"}, "request")
        request_id = _id(request["request_id"], "request id")
        if request_id in used:
            raise ValueError("duplicate request id")
        used.add(request_id)
        truth = request["ground_truth_id"]
        if truth is not None:
            truth = _id(truth, "ground truth id")
        candidates = request["candidates"]
        # Validate every method identically before evaluating the first outcome.
        decisions = {method: select_instance(candidates, method, threshold, margin)
                     for method in METHODS}
        for method, decision in decisions.items():
            status = _outcome(decision["selected_id"], truth)
            trials.append({"request_id": request_id, "method": method,
                           "target_present": truth is not None,
                           "ground_truth_id": truth,
                           **decision, "status": status,
                           "wrong_selection": status == "wrong_selection"})
    summary = {}
    for method in METHODS:
        rows = [trial for trial in trials if trial["method"] == method]
        n = len(rows)
        counts = {status: sum(row["status"] == status for row in rows)
                  for status in ("correct_selection", "correct_rejection",
                                 "wrong_selection", "abstained")}
        summary[method] = {
            "eligible_requests": n, **counts,
            "wrong_selection_rate": counts["wrong_selection"] / n,
            "abstention_rate": sum(row["selected_id"] is None for row in rows) / n,
        }
    return {
        "schema_version": VERSION, "evidence_type": "fixture",
        "stage": "synthetic_software_check_not_scientific_evidence",
        "suite_id": suite_id, "source": software_provenance(),
        "input_sha256": sha256_file(path),
        "threshold": threshold, "ambiguity_margin": margin,
        "trials": trials, "summary": summary,
    }
