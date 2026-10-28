"""Conservative colour-cue extraction from supplied car masks in actual images.

This is *not* a vehicle detector, car re-identification, instruction parser
or calibrated classifier. In particular, one leading candidate is only a
hint requiring independent target confirmation before robot action.
"""
from __future__ import annotations

from pathlib import Path

from .vehicle_image_quality import (
    _file_and_hash, _load_pixels, _str, _unit, _byte, MAX_PIXELS
)

_COLOURS = {"red", "green", "blue", "yellow"}
_MAX_CANDIDATES = 32


def _colour(r: int, g: int, b: int) -> str:
    """Fixed coarse RGB baseline; deliberately not learned/calibrated."""
    if (r > 1.35*b and g > 1.35*b and abs(r-g) <= 30):
        return "yellow"
    if r > 1.3*g and r > 1.3*b:
        return "red"
    if g > 1.3*r and g > 1.3*b:
        return "green"
    if b > 1.3*r and b > 1.3*g:
        return "blue"
    return "other"


def propose_colour_targets(spec: dict, data_root: Path) -> dict:
    """Return color-cue candidates, never an authoritative selected car."""
    if not isinstance(spec, dict) or spec.get("schema_version") != 1:
        raise ValueError("unsupported colour cue schema")
    req = spec.get("request")
    if not isinstance(req, dict) or req.get("requested_colour") not in _COLOURS:
        raise ValueError("request must declare one supported colour")
    colour = req["requested_colour"]
    _str(req.get("utterance_id"), "utterance_id")
    _str(req.get("observation_frame_id"), "observation_frame_id")
    policy = spec.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("policy object required")
    chroma_min = _byte(policy.get("minimum_chroma"), "minimum_chroma")
    intensity_min = _byte(policy.get("minimum_intensity"), "minimum_intensity")
    intensity_max = _byte(policy.get("maximum_intensity"), "maximum_intensity")
    if intensity_min >= intensity_max:
        raise ValueError("intensity range invalid")
    min_roi = policy.get("minimum_mask_pixels")
    if type(min_roi) is not int or not 1 <= min_roi <= MAX_PIXELS:
        raise ValueError("minimum_mask_pixels invalid")
    min_usable = _unit(policy.get("minimum_usable_fraction"), "minimum_usable_fraction")
    min_match = _unit(policy.get("minimum_matching_fraction"), "minimum_matching_fraction")
    image_path, raw, image_hash = _file_and_hash(data_root, spec.get("image"), "image")
    width, height, pixels = _load_pixels(image_path, raw, mask=False)
    candidates = spec.get("candidates")
    if not isinstance(candidates, list) or len(candidates) > _MAX_CANDIDATES:
        raise ValueError("candidate list invalid or exceeds 32")
    ids = set()
    scored = []
    hints = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be an object")
        identifier = _str(candidate.get("vehicle_instance_id"), "vehicle_instance_id")
        if identifier in ids:
            raise ValueError("duplicate vehicle instance ID")
        ids.add(identifier)
        _str(candidate.get("mask_annotation_id"), "mask_annotation_id")
        _str(candidate.get("annotation_origin"), "annotation_origin")
        path, mask_raw, mask_hash = _file_and_hash(data_root, candidate.get("car_body_mask"), "car_body_mask")
        mask_width, mask_height, mask = _load_pixels(path, mask_raw, mask=True)
        if (width, height) != (mask_width, mask_height):
            raise ValueError("body mask and image dimensions differ")
        pixels_in_roi = usable = matched = 0
        for i, included in enumerate(mask):
            if not included:
                continue
            pixels_in_roi += 1
            r, g, b = pixels[3*i:3*i+3]
            hi, lo = max(r, g, b), min(r, g, b)
            if (hi-lo < chroma_min or hi < intensity_min or hi > intensity_max):
                continue
            usable += 1
            if _colour(r, g, b) == colour:
                matched += 1
        usable_fraction = usable / pixels_in_roi if pixels_in_roi else 0.0
        matching_fraction = matched / usable if usable else 0.0
        evidence_ok = (pixels_in_roi >= min_roi
                       and usable_fraction >= min_usable
                       and matching_fraction >= min_match)
        if evidence_ok:
            hints.append(identifier)
        scored.append({
            "vehicle_instance_id": identifier,
            "car_body_mask_sha256": mask_hash,
            "mask_pixels": pixels_in_roi,
            "usable_colour_pixels": usable,
            "matching_colour_pixels": matched,
            "usable_fraction": usable_fraction,
            "matching_fraction_among_usable": matching_fraction,
            "candidate_colour_cue": evidence_ok,
        })
    if not hints:
        status = "no_supported_colour_candidate"
    elif len(hints) > 1:
        status = "ambiguous_multiple_colour_candidates"
    else:
        status = "single_unverified_colour_candidate"
    return {
        "schema_version": 1,
        "image_sha256": image_hash,
        "requested_colour": colour,
        "status": status,
        "candidate_instance_ids": sorted(hints),
        "ranked_evidence": sorted(scored, key=lambda x: x["vehicle_instance_id"]),
        "colour_algorithm": "fixed_rgb_dominance_fixture_baseline_not_calibrated",
        "identity_confirmed": False,
        "part_recognized": False,
        "safe_to_start_physical_inspection": False,
        "observed_image_evidence": True,
        "independent_annotations_required": True,
    }
