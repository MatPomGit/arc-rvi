"""Offline evidence-contract evaluator for commanded vehicle photography.

No perception, natural-language model, ROS adapter, path planner, camera or
robot controller is implemented here. The caller supplies bounded observations;
every image, target and return claim is assessed against independent fields.
"""
from __future__ import annotations

import math
import re

_HEX256 = re.compile(r"[0-9a-f]{64}\Z")
_PARTS = {"front_bumper", "rear_bumper", "hood", "roof", "trunk",
          "front_left_door", "front_right_door", "rear_left_door",
          "rear_right_door", "left_fender", "right_fender",
          "left_headlamp", "right_headlamp", "other_component"}


def _mapping(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _array(value, name):
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def _flag(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _fraction(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a finite fraction in [0, 1]")
    return float(value)


def _unique_ids(items, name):
    values = [_text(_mapping(x, name).get("id"), f"{name}.id") for x in items]
    if len(values) != len(set(values)):
        raise ValueError(f"{name} contains duplicate IDs")


def assess_mission(data: dict) -> dict:
    """Evaluate a *fixture-only* mission trace; never command real movement.

    The completeness denominator is the independently predeclared shot list,
    not the number of photos taken. Rejected shots can be reacquired, but an
    unverified identity or physical return can never pass by high image quality.
    """
    d = _mapping(data, "mission")
    if d.get("schema_version") != 1 or d.get("execution_mode") != "fixture_only":
        raise ValueError("unsupported schema or non-fixture execution mode")
    mission_id = _text(d.get("mission_id"), "mission_id")
    origin = _text(d.get("handoff_anchor_id"), "handoff_anchor_id")
    command = _mapping(d.get("command"), "command")
    _text(command.get("text"), "command.text")
    _text(command.get("vehicle_description"), "command.vehicle_description")
    scope = command.get("scope")
    if scope not in ("vehicle", "component"):
        raise ValueError("scope must be vehicle or component")
    component = command.get("component")
    if scope == "component" and component not in _PARTS:
        raise ValueError("component must be an explicit supported part label")
    if scope == "vehicle" and component is not None:
        raise ValueError("whole vehicle must not encode one component")

    plan = _mapping(d.get("shot_plan"), "shot_plan")
    if plan.get("approval_kind") not in ("operator_approved", "versioned_protocol"):
        raise ValueError("shot list must be approved or versioned")
    _text(plan.get("approval_ref"), "shot_plan.approval_ref")
    requirements = _array(plan.get("required"), "shot_plan.required")
    if not requirements:
        raise ValueError("shot_plan.required cannot be empty")
    req_by_id = {}
    for req in requirements:
        req = _mapping(req, "shot requirement")
        slot = _text(req.get("slot_id"), "slot_id")
        part = _text(req.get("part"), "required.part")
        view = _text(req.get("view"), "required.view")
        if slot in req_by_id:
            raise ValueError("duplicate required shot slot_id")
        if scope == "component" and part != component:
            raise ValueError("component mission has a requirement for another part")
        if scope == "vehicle" and part not in _PARTS | {"whole_vehicle"}:
            raise ValueError("unknown whole-vehicle requirement part")
        req_by_id[slot] = (part, view)

    limits = _mapping(d.get("quality_limits"), "quality_limits")
    max_glare = _fraction(limits.get("max_glare_fraction"), "max_glare_fraction")
    max_occlusion = _fraction(limits.get("max_occlusion_fraction"), "max_occlusion_fraction")

    grounding = _mapping(d.get("target_grounding"), "target_grounding")
    candidates = _array(grounding.get("candidates"), "target_grounding.candidates")
    for item in candidates:
        _mapping(item, "candidate")
        _flag(item.get("matches_description"), "candidate.matches_description")
    _unique_ids(candidates, "candidates")
    matches = {x["id"] for x in candidates if x["matches_description"]}
    decision = _mapping(grounding.get("decision"), "target_grounding.decision")
    status = decision.get("status")
    if status not in ("resolved", "ambiguous", "absent"):
        raise ValueError("target decision status unsupported")
    chosen = decision.get("selected_instance_id")
    clarified = _flag(decision.get("clarification_confirmed"), "clarification_confirmed")
    obs = _array(decision.get("observation_ids"), "target_grounding.observation_ids")
    if any(not isinstance(x, str) or not x.strip() for x in obs):
        raise ValueError("grounding observation IDs must be nonempty text")

    violations = []
    target_ok = False
    if status == "resolved":
        if not isinstance(chosen, str) or chosen not in matches:
            violations.append("target_not_grounded_in_matching_observation")
        elif not obs:
            violations.append("target_without_observation_provenance")
        elif len(matches) > 1 and not clarified:
            violations.append("unresolved_multi_car_ambiguity")
        else:
            target_ok = True
    elif chosen is not None:
        violations.append("unresolved_decision_carries_target")
    if status == "absent" and matches:
        violations.append("absent_target_with_matching_candidates")

    part_ok = scope == "vehicle"
    if scope == "component":
        part_data = _mapping(d.get("part_grounding"), "part_grounding")
        if (part_data.get("status") == "resolved"
                and part_data.get("part_label") == component
                and part_data.get("parent_instance_id") == chosen
                and isinstance(part_data.get("observation_ids"), list)
                and len(part_data["observation_ids"]) > 0
                and all(isinstance(v, str) and v.strip()
                        for v in part_data["observation_ids"])
                and target_ok):
            part_ok = True
        else:
            violations.append("part_not_localized_on_selected_car")
    elif d.get("part_grounding") is not None:
        raise ValueError("unexpected part_grounding for vehicle mission")

    attempts = _array(d.get("photo_attempts"), "photo_attempts")
    _unique_ids(attempts, "photo_attempts")
    if attempts and not target_ok:
        violations.append("premature_photography_without_verified_target")
    selected = set()
    seen_hashes = set()
    rejected = []
    for photo in attempts:
        _mapping(photo, "photo")
        pid = photo["id"]
        slot = _text(photo.get("slot_id"), "photo.slot_id")
        image_hash = _text(photo.get("image_sha256"), "photo.image_sha256")
        if not _HEX256.fullmatch(image_hash):
            raise ValueError("photo image_sha256 must be a lowercase 64-character digest")
        if image_hash in seen_hashes:
            violations.append("duplicate_image_digest")
        seen_hashes.add(image_hash)
        _text(photo.get("observation_id"), "photo.observation_id")
        qc = _mapping(photo.get("independent_qc"), "photo.independent_qc")
        _flag(qc.get("reference_separate_from_policy"), "reference_separate_from_policy")
        glare = _fraction(qc.get("glare_fraction"), "glare_fraction")
        occlusion = _fraction(qc.get("occlusion_fraction"), "occlusion_fraction")
        for k in ("framing_ok", "focus_ok", "exposure_ok"):
            _flag(qc.get(k), f"independent_qc.{k}")
        reasons = []
        if not target_ok or not part_ok:
            reasons.append("unresolved_grounding")
        if slot not in req_by_id:
            reasons.append("unassigned_shot")
        elif (photo.get("part"), photo.get("view")) != req_by_id[slot]:
            reasons.append("wrong_part_or_view")
        if photo.get("vehicle_instance_id") != chosen:
            reasons.append("wrong_vehicle_identity")
            violations.append("photo_taken_of_wrong_vehicle")
        if not qc["reference_separate_from_policy"]:
            reasons.append("quality_not_independently_evaluated")
        if glare > max_glare:
            reasons.append("specular_glare")
        if occlusion > max_occlusion:
            reasons.append("occlusion")
        if not qc["framing_ok"]:
            reasons.append("framing")
        if not qc["focus_ok"]:
            reasons.append("focus")
        if not qc["exposure_ok"]:
            reasons.append("exposure")
        if image_hash in (r["image_sha256"] for r in rejected):
            reasons.append("reused_rejected_image")
        if reasons:
            rejected.append({"attempt_id": pid, "image_sha256": image_hash, "reasons": reasons})
        else:
            selected.add(slot)

    returned = _mapping(d.get("return_evidence"), "return_evidence")
    _text(returned.get("anchor_id"), "return_evidence.anchor_id")
    if returned.get("status") not in ("arrived", "blocked", "not_attempted"):
        raise ValueError("unsupported return status")
    safe_route = _flag(returned.get("safe_route_verified"), "safe_route_verified")
    handoff = _flag(returned.get("operator_handoff_confirmed"), "operator_handoff_confirmed")
    return_ok = (returned["anchor_id"] == origin and returned["status"] == "arrived"
                 and safe_route and handoff)

    missed = sorted(set(req_by_id) - selected)
    if not target_ok:
        verdict = "blocked_target"
    elif not part_ok:
        verdict = "blocked_part"
    elif violations:
        verdict = "invalid_trace"
    elif missed:
        verdict = "partial_coverage"
    elif not return_ok:
        verdict = "return_unverified"
    else:
        verdict = "fixture_complete"

    return {
        "mission_id": mission_id,
        "verdict": verdict,
        "assigned_slots": len(req_by_id),
        "accepted_slots": len(selected),
        "missing_slots": missed,
        "rejected_attempts": rejected,
        "trace_violations": sorted(set(violations)),
        "target_grounded": target_ok,
        "part_grounded": part_ok,
        "return_verified": return_ok,
        "evidence_class": "software_fixture_only",
        "physical_robot_success": False,
    }
