"""Deterministic instance assignment on supplied fixture distances only.

No image features, camera pose, sensor fusion or physical localization is
computed here. Ground truth is passed only to the separate evaluator.
"""
from __future__ import annotations

import json
from hashlib import sha256
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

# Sensor comparisons reuse the fixture selector with honest method labels.
# Pixel bearing is not a learned visual descriptor or physical pose estimate.
SENSOR_METHODS = {
    "bearing_proxy": "visual",
    "range_proxy": "spatial",
    "joint_proxy": "fused",
}

IMAGE_METHODS = {
    "grayscale_mae": "visual",
    "range_proxy": "spatial",
    "grayscale_range": "fused",
}


def _study_file(study_path: Path, relative: object) -> Path:
    """Confine included files to the study directory's parent data tree."""
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("study input needs a relative path")
    root = study_path.resolve(strict=True).parent.parent
    target = (study_path.parent / relative).resolve(strict=True)
    if not target.is_file() or not target.is_relative_to(root):
        raise ValueError("study input path escapes the study data tree")
    return target


def run_sensor_localization(study_path: Path) -> dict:
    """Compare bearing/range association on actual synthetic sensor features.

    The target cue is an externally supplied expected pixel/range pair.
    Reference patch identities are accessed only after all method selections.
    """
    from .adapters.simulator import PlanarSimulator, load_scene
    from .perception import load_sensor_config, simulate_sensor
    from .image_features import pixel_distance, render_patch, validate_pixels
    from .scenarios import read_json

    spec, raw = read_json(Path(study_path))
    image_mode = spec.get("schema_version") == "1.1.0"
    expected = {"schema_version", "study_id", "evidence_type", "stage",
                "suite_id", "scene", "sensor", "threshold",
                "ambiguity_margin", "requests"}
    if image_mode:
        expected |= {"appearance", "session_id"}
    _fields(spec, expected, "sensor study")
    if (spec["schema_version"], spec["study_id"], spec["evidence_type"],
            spec["stage"]) not in (
                ("1.0.0", "02", "simulation", "exploratory_not_confirmatory"),
                ("1.1.0", "02", "simulation", "exploratory_not_confirmatory")):
        raise ValueError("unsupported or non-exploratory sensor study")
    suite_id = _id(spec["suite_id"], "suite id")
    threshold = _fraction(spec["threshold"], "threshold")
    margin = _fraction(spec["ambiguity_margin"], "ambiguity_margin")
    scene_path = _study_file(Path(study_path), spec["scene"])
    sensor_path = _study_file(Path(study_path), spec["sensor"])
    scene, _ = load_scene(scene_path)
    sensor, _ = load_sensor_config(sensor_path)
    PlanarSimulator(scene)  # Fail invalid geometric and motion models up front.
    patch_ids = {patch.identifier for patch in scene.patches}
    requests = spec["requests"]
    if not isinstance(requests, list) or not 1 <= len(requests) <= 256:
        raise ValueError("sensor study requires 1 to 256 target requests")
    observed_ids = set()
    rows, observations = [], []
    methods = IMAGE_METHODS if image_mode else SENSOR_METHODS
    if image_mode:
        appearance = _fields(spec["appearance"], {"textures", "noise_seed"},
                             "appearance")
        texture_map = _fields(appearance["textures"], {"target", "distractor"},
                              "appearance textures")
        texture_map = {key: validate_pixels(value)
                       for key, value in texture_map.items()}
        noise_seed = appearance["noise_seed"]
        if type(noise_seed) is not int or not 0 <= noise_seed < 2**64:
            raise ValueError("appearance noise seed must be unsigned 64-bit integer")
        session_id = _id(spec["session_id"], "session id")
    for request in requests:
        request_fields = {"request_id", "capture_index", "expected_u_px",
                          "expected_range_m", "ground_truth_patch_id"}
        if image_mode:
            request_fields |= {"template_pixels", "timestamp_s"}
        _fields(request, request_fields, "target request")
        request_id = _id(request["request_id"], "request id")
        if request_id in observed_ids:
            raise ValueError("duplicate target request id")
        observed_ids.add(request_id)
        capture_index = request["capture_index"]
        if type(capture_index) is not int or not 0 <= capture_index < 2**32:
            raise ValueError("capture_index must be an unsigned 32-bit integer")
        u = request["expected_u_px"]
        expected_range = request["expected_range_m"]
        if (type(u) not in (int, float) or not isfinite(u)
                or not 0 <= u <= sensor.width_px):
            raise ValueError("invalid requested horizontal pixel")
        if (type(expected_range) not in (int, float)
                or not isfinite(expected_range)
                or not 0 <= expected_range <= scene.camera.max_range_m):
            raise ValueError("invalid requested range in metres")
        # Ground truth is validated but is NEVER part of candidate construction.
        truth = request["ground_truth_patch_id"]
        if truth is not None and (type(truth) is not str or truth not in patch_ids):
            raise ValueError("unknown evaluator-only patch identity")
        timestamp_s = request["timestamp_s"] if image_mode else 0.0
        if image_mode and (type(timestamp_s) not in (int, float)
                           or not isfinite(timestamp_s) or timestamp_s < 0):
            raise ValueError("invalid observation timestamp")
        policy, reference = simulate_sensor(
            scene, scene.start, sensor, capture_index=capture_index,
            timestamp_s=timestamp_s)
        if image_mode:
            template = validate_pixels(request["template_pixels"])
            # Privileged simulator stage produces pixels. Only anonymous pixels
            # and the request template cross the boundary to the selector.
            renderer_labels = {
                item["detection_id"]: item["patch_id"]
                for item in reference["geometry_references"]
                if item["detection_id"] is not None
            }
            anonymous = []
            for detection in policy["detections"]:
                identity = renderer_labels[detection["id"]]
                pixels = render_patch(texture_map[identity], noise_seed,
                                      session_id, capture_index, identity)
                anonymous.append({**detection, "gray8_8x8": pixels})
            policy = {**policy, "detections": anonymous,
                      "image_model": "synthetic_grayscale_patch_v1"}
        candidates = [{
            "id": detection["id"],
            "visual_distance": (pixel_distance(
                template, detection["gray8_8x8"]) if image_mode
                else abs(detection["u_px"] - u) / sensor.width_px),
            "spatial_distance": min(
                1.0, abs(detection["range_m"] - expected_range)
                / scene.camera.max_range_m),
        } for detection in policy["detections"]]
        decisions = {label: select_instance(candidates, internal, threshold, margin)
                     for label, internal in methods.items()}
        # Only the evaluator reads identity correspondence after predictions.
        visible_truth = {item["detection_id"]: item["patch_id"]
                         for item in reference["geometry_references"]
                         if item["detection_id"] is not None}
        observations.append({"request_id": request_id, "policy": policy,
                             "evaluator": reference})
        for method, decision in decisions.items():
            predicted = visible_truth.get(decision["selected_id"])
            # Absent reference target + any selection is a wrong selection.
            outcome = _outcome(predicted if decision["selected_id"] else None, truth)
            rows.append({
                "request_id": request_id, "capture_index": capture_index,
                "method": method, "selected_id": decision["selected_id"],
                "selected_reference_patch_id": predicted,
                "ground_truth_patch_id": truth, "score": decision["score"],
                "decision": decision["decision"], "status": outcome,
                "wrong_selection": outcome == "wrong_selection",
                "target_present": truth is not None,
                "measurement_status": policy["status"],
                **({"session_id": session_id, "timestamp_s": timestamp_s}
                   if image_mode else {}),
            })
    summary = {}
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        counts = {label: sum(row["status"] == label for row in method_rows)
                  for label in ("correct_selection", "correct_rejection",
                                "wrong_selection", "abstained")}
        n = len(method_rows)
        summary[method] = {
            "eligible_requests": n, **counts,
            "wrong_selection_rate": counts["wrong_selection"] / n,
            "correct_selection_rate": counts["correct_selection"] / n,
            "abstention_rate": sum(r["selected_id"] is None for r in method_rows) / n,
            "missing_frames": sum(r["measurement_status"] == "measurement_missing"
                                  for r in method_rows),
        }
    return {
        "schema_version": "1.0.0", "evidence_type": "simulation",
        "status": "exploratory_not_confirmatory", "study_id": "02",
        "suite_id": suite_id,
        "model": ("synthetic_grayscale_patch_plus_planar_range_v1"
                  if image_mode else "planar_bearing_range_proxy_v1"),
        "independent_unit": "one_hand_constructed_scene_not_population",
        "selection_modes": list(methods),
        "method_semantics": ({
            "grayscale_mae": "normalized_gray8_patch_mean_absolute_error",
            "range_proxy": "normalized_planar_range_discrepancy",
            "grayscale_range": "equal_weight_grayscale_and_range_proxy",
        } if image_mode else {
            "bearing_proxy": "horizontal_pixel_difference_not_appearance",
            "range_proxy": "sensor_range_difference_not_3d_pose",
            "joint_proxy": "equal_weight_normalized_bearing_range",
        }),
        "source": software_provenance(),
        "input_sha256": sha256(raw).hexdigest(),
        "scene_sha256": sha256_file(scene_path),
        "sensor_sha256": sha256_file(sensor_path),
        "visibility_access": "evaluator_only_geometry",
        "threshold": threshold, "ambiguity_margin": margin,
        **({"session_id": session_id} if image_mode else {}),
        "observations": observations, "trials": rows, "summary": summary,
    }
