"""Offline P02 image-crop association with separate evaluator annotations.

Accepts operator-supplied PGM crops and measured/declared range cues. This
module does not calibrate the camera, establish independent reference truth,
or claim physical localization accuracy.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import isfinite
from pathlib import Path

from .evidence import digest, sha256_file, software_provenance
from .localization import select_instance
from .scenarios import read_json

METHODS = {"image_mae": "visual", "range_only": "spatial",
           "image_range": "fused"}
MAX_BYTES = 131072
MAX_PIXELS = 65536
MAX_SESSIONS = 32
MAX_REQUESTS = 64
MAX_CANDIDATES = 16


def _fields(value: object, expected: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"invalid {name} fields")
    return value


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip() or len(value) > 128:
        raise ValueError(f"invalid {name}")
    return value


def _number(value: object, name: str, upper: float) -> float:
    if type(value) not in (float, int) or not isfinite(value) or not 0 <= value <= upper:
        raise ValueError(f"invalid {name}")
    return float(value)


def _safe_file(root: Path, entry: object, *, maximum: int) -> Path:
    entry = _fields(entry, {"path", "sha256"}, "hash record")
    relative, checksum = entry["path"], entry["sha256"]
    if (type(relative) is not str or not relative
            or Path(relative).is_absolute() or ".." in Path(relative).parts
            or type(checksum) is not str or len(checksum) != 64
            or any(c not in "0123456789abcdef" for c in checksum)):
        raise ValueError("invalid relative path or SHA-256")
    try:
        target = (root / relative).resolve(strict=True)
    except OSError as exc:
        raise ValueError("missing input file") from exc
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("file escapes dataset directory")
    if target.stat().st_size > maximum:
        raise ValueError("input exceeds byte limit")
    if sha256_file(target) != checksum:
        raise ValueError("input SHA-256 mismatch")
    return target


def _pgm_token(raw: bytes, offset: int) -> tuple[bytes, int]:
    length = len(raw)
    while offset < length:
        if raw[offset] in b" \t\r\n":
            offset += 1
        elif raw[offset] == 35:
            end = raw.find(b"\n", offset)
            if end == -1:
                raise ValueError("incomplete PGM comment")
            offset = end + 1
        else:
            break
    start = offset
    while offset < length and raw[offset] not in b" \t\r\n#":
        offset += 1
    if offset == start:
        raise ValueError("missing PGM header or pixel token")
    return raw[start:offset], offset


def read_pgm(path: Path) -> tuple[int, int, bytes]:
    """Strict P2/P5 8-bit PGM reader; no third-party dependencies or resizing."""
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("PGM exceeds byte limit")
    raw = path.read_bytes()
    offset = 0
    try:
        magic, offset = _pgm_token(raw, offset)
        width_raw, offset = _pgm_token(raw, offset)
        height_raw, offset = _pgm_token(raw, offset)
        max_raw, offset = _pgm_token(raw, offset)
        width, height, maximum = int(width_raw), int(height_raw), int(max_raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid PGM header") from exc
    if (magic not in (b"P2", b"P5") or not 1 <= width <= 256
            or not 1 <= height <= 256 or width * height > MAX_PIXELS
            or maximum != 255):
        raise ValueError("unsupported PGM format, dimensions or max value")
    if magic == b"P5":
        if offset >= len(raw) or raw[offset] not in b" \t\r\n":
            raise ValueError("P5 binary data needs one whitespace separator")
        offset += 1
        if raw[offset - 1:offset] == b"\r" and raw[offset:offset + 1] == b"\n":
            offset += 1
        pixels = raw[offset:]
        if len(pixels) != width * height:
            raise ValueError("invalid P5 pixel count")
    else:
        values = []
        for _ in range(width * height):
            token, offset = _pgm_token(raw, offset)
            try:
                value = int(token)
            except ValueError as exc:
                raise ValueError("invalid P2 pixel value") from exc
            if not 0 <= value <= 255:
                raise ValueError("P2 values must be uint8")
            values.append(value)
        # Reject extra tokens; trailing comments and whitespace are accepted.
        try:
            _pgm_token(raw, offset)
        except ValueError:
            pass
        else:
            raise ValueError("extra P2 pixel data")
        pixels = bytes(values)
    return width, height, pixels


def _image(root: Path, entry: object) -> tuple[int, int, bytes]:
    return read_pgm(_safe_file(root, entry, maximum=MAX_BYTES))


def _distance(a: tuple[int, int, bytes], b: tuple[int, int, bytes]) -> float:
    if a[:2] != b[:2]:
        raise ValueError("image crops require equal pixel dimensions")
    return sum(abs(x - y) for x, y in zip(a[2], b[2])) / (len(a[2]) * 255)


def _utc(value: object) -> datetime:
    if type(value) is not str or len(value) > 40:
        raise ValueError("invalid UTC timestamp")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid UTC timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must include a timezone offset")
    return timestamp


def _predictions(root: Path, observed: dict, threshold: float,
                 margin: float, max_range: float) -> tuple[list[dict], dict[str, set[str]]]:
    _fields(observed, {"schema_version", "session_id", "requests"}, "observations")
    if observed["schema_version"] != "1.0.0":
        raise ValueError("unsupported observation schema")
    requests = observed["requests"]
    if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_REQUESTS:
        raise ValueError("session request count exceeds supported limit")
    results: list[dict] = []
    seen: set[str] = set()
    candidate_ids: dict[str, set[str]] = {}
    previous_time = None
    for request in requests:
        _fields(request, {"request_id", "timestamp_utc", "status", "template",
                          "expected_range_m", "candidates"}, "request")
        request_id = _text(request["request_id"], "request id")
        if request_id in seen:
            raise ValueError("duplicate request id")
        seen.add(request_id)
        timestamp = _utc(request["timestamp_utc"])
        if previous_time is not None and timestamp < previous_time:
            raise ValueError("timestamps must be monotonic within session")
        previous_time = timestamp
        if request["status"] not in ("captured", "missing_frame"):
            raise ValueError("invalid observation status")
        template = _image(root, request["template"])
        expected = _number(request["expected_range_m"], "expected range", max_range)
        detections = request["candidates"]
        if not isinstance(detections, list) or len(detections) > MAX_CANDIDATES:
            raise ValueError("invalid candidate count")
        if request["status"] == "missing_frame" and detections:
            raise ValueError("missing frame cannot contain detections")
        candidates = []
        ids = set()
        for detection in detections:
            _fields(detection, {"id", "range_m", "image"}, "candidate")
            identifier = _text(detection["id"], "candidate id")
            if identifier in ids:
                raise ValueError("duplicate candidate id")
            ids.add(identifier)
            candidates.append({
                "id": identifier,
                "visual_distance": _distance(template, _image(root, detection["image"])),
                "spatial_distance": abs(expected - _number(
                    detection["range_m"], "candidate range", max_range)) / max_range,
            })
        candidate_ids[request_id] = ids
        for label, method in METHODS.items():
            decision = select_instance(candidates, method, threshold, margin)
            results.append({
                "request_id": request_id, "timestamp_utc": request["timestamp_utc"],
                "measurement_status": request["status"], "method": label, **decision,
            })
    return results, candidate_ids


def _score(predictions: list[dict], reference: dict,
           candidate_ids: dict[str, set[str]],
           session_id: str, family: str) -> list[dict]:
    _fields(reference, {"schema_version", "session_id", "labels"}, "reference")
    if reference["schema_version"] != "1.0.0" or reference["session_id"] != session_id:
        raise ValueError("reference session does not match observations")
    labels = reference["labels"]
    if not isinstance(labels, list) or len(labels) != len(candidate_ids):
        raise ValueError("reference request count does not match observations")
    truth = {}
    for label in labels:
        _fields(label, {"request_id", "target_present", "target_candidate_id"}, "label")
        request_id = _text(label["request_id"], "reference request id")
        present, chosen = label["target_present"], label["target_candidate_id"]
        if (request_id in truth or type(present) is not bool
                or (chosen is not None and (not present or type(chosen) is not str
                                             or not chosen.strip()))):
            raise ValueError("invalid or duplicate reference identity")
        if chosen is not None and chosen not in candidate_ids.get(request_id, set()):
            raise ValueError("reference points to an unknown detection")
        truth[request_id] = (present, chosen)
    if set(truth) != set(candidate_ids):
        raise ValueError("reference request IDs do not match observations")
    scored = []
    for prediction in predictions:
        present, truth_id = truth[prediction["request_id"]]
        selected = prediction["selected_id"]
        outcome = ("correct_selection" if selected == truth_id and selected is not None
                   else "wrong_selection" if selected is not None
                   else "abstained" if present else "correct_rejection")
        scored.append({
            **prediction, "session_id": session_id, "object_family_id": family,
            "target_present": present, "status": outcome,
            "wrong_selection": outcome == "wrong_selection",
        })
    return scored


def _summary(rows: list[dict]) -> dict:
    n = len(rows)
    counts = {key: sum(row["status"] == key for row in rows) for key in (
        "correct_selection", "correct_rejection", "wrong_selection", "abstained")}
    return {
        "eligible_requests": n, **counts,
        "wrong_selection_rate": counts["wrong_selection"] / n,
        "abstention_rate": sum(row["selected_id"] is None for row in rows) / n,
        "missing_frames": sum(row["measurement_status"] == "missing_frame"
                              for row in rows),
    }


def evaluate_image_manifest(manifest_path: Path, partition: str = "pilot") -> dict:
    """Analyze only a declared exploratory partition, never open holdout records."""
    if partition not in ("development", "pilot"):
        raise ValueError("holdout replay is prohibited in exploratory mode")
    manifest_path = Path(manifest_path)
    manifest, raw = read_json(manifest_path)
    _fields(manifest, {"schema_version", "study_id", "evidence_type", "stage",
                       "data_origin", "data_rights", "threshold",
                       "ambiguity_margin", "max_range_m", "records"}, "manifest")
    if (manifest["schema_version"], manifest["study_id"],
            manifest["evidence_type"], manifest["stage"]) != (
                "1.0.0", "02", "image_observation", "exploratory_not_confirmatory"):
        raise ValueError("unsupported image-manifest schema")
    if manifest["data_origin"] not in ("synthetic_test", "operator_supplied"):
        raise ValueError("invalid declared data origin")
    if manifest["data_rights"] != "operator_declared_authorized":
        raise ValueError("data rights must be declared by the operator")
    threshold = _number(manifest["threshold"], "threshold", 1)
    margin = _number(manifest["ambiguity_margin"], "ambiguity margin", 1)
    max_range = _number(manifest["max_range_m"], "maximum range", 100000)
    if max_range <= 0:
        raise ValueError("maximum range must be positive")
    records = manifest["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_SESSIONS:
        raise ValueError("invalid session record count")
    root = manifest_path.resolve(strict=True).parent
    families: dict[str, str] = {}
    sessions = set()
    selected = []
    for record in records:
        _fields(record, {"partition", "object_family_id", "session_id",
                         "observations", "reference"}, "session record")
        part = record["partition"]
        if part not in ("development", "pilot", "holdout"):
            raise ValueError("invalid partition")
        family = _text(record["object_family_id"], "object family id")
        session = _text(record["session_id"], "session id")
        if session in sessions or (family in families and families[family] != part):
            raise ValueError("duplicate session or family crossing partitions")
        sessions.add(session)
        families[family] = part
        # No holdout file is opened or hashed during exploratory replay.
        if part == partition:
            selected.append(record)
    if not selected:
        raise ValueError("no session records for selected partition")
    all_rows = []
    for record in selected:
        obs_path = _safe_file(root, record["observations"], maximum=MAX_BYTES)
        observed, _ = read_json(obs_path)
        if observed.get("session_id") != record["session_id"]:
            raise ValueError("observation session differs from manifest")
        # Only observations and pixel crops reach the policy.
        decisions, candidate_ids = _predictions(
            root, observed, threshold, margin, max_range)
        # Load evaluator-only truth after all decisions for this session.
        reference_path = _safe_file(root, record["reference"], maximum=MAX_BYTES)
        reference, _ = read_json(reference_path)
        all_rows.extend(_score(decisions, reference, candidate_ids,
                               record["session_id"],
                               record["object_family_id"]))
    groups: dict[str, list[dict]] = defaultdict(list)
    sessions: dict[str, list[dict]] = defaultdict(list)
    strata: dict[str, list[dict]] = defaultdict(list)
    for trial in all_rows:
        groups[trial["object_family_id"]].append(trial)
        sessions[trial["session_id"]].append(trial)
        strata["present" if trial["target_present"] else "absent"].append(trial)
    family_summary = {
        family: {method: _summary([r for r in rows if r["method"] == method])
                 for method in METHODS}
        for family, rows in sorted(groups.items())
    }
    session_summary = {
        session: {method: _summary([r for r in rows if r["method"] == method])
                  for method in METHODS}
        for session, rows in sorted(sessions.items())
    }
    family_mean = {
        method: sum(group[method]["wrong_selection_rate"]
                    for group in family_summary.values()) / len(family_summary)
        for method in METHODS
    }
    return {
        "schema_version": "1.0.0", "study_id": "02",
        "evidence_type": "image_observation",
        "status": "exploratory_not_confirmatory",
        "data_origin": manifest["data_origin"],
        "data_rights": "operator_declaration_not_independently_verified",
        "partition": partition, "independent_unit": "declared_object_family",
        "family_count": len(family_summary), "session_count": len(selected),
        "methods": list(METHODS), "manifest_sha256": digest(raw),
        "source": software_provenance(),
        "family_summary": family_summary, "session_summary": session_summary,
        "mean_family_wrong_risk": family_mean,
        "paired_difference_fusion_minus_image": (
            family_mean["image_range"] - family_mean["image_mae"]),
        "target_strata": {
            name: {method: _summary([r for r in rows if r["method"] == method])
                   for method in METHODS}
            for name, rows in sorted(strata.items())
        },
        "trials": all_rows,
        "inference": "descriptive_only_no_ci_no_p_value",
        "limitations": ("PGM_crops_and_range_input_are_operator_supplied;"
                        "no_calibration_or_reference_truth_verification;"
                        "no_sealed_confirmatory_data"),
    }
