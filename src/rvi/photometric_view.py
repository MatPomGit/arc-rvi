"""A conservative, deterministic *fixture-only* car-camera viewpoint selector.

Requires externally supplied *predictions* and static feasibility proxies.
It does not sense glare, perform BRDF ray tracing, optimise locomotion,
validate physical robot safety or issue motor/camera commands.
"""
from __future__ import annotations

import math


def _number(x, name, *, low=0.0, high=float("inf")):
    if type(x) not in (float, int) or not math.isfinite(x) or not low <= x <= high:
        raise ValueError(f"{name} must be finite within [{low}, {high}]")
    return float(x)


def _boolean(x, name):
    if type(x) is not bool:
        raise ValueError(f"{name} must be bool")
    return x


def select_view(spec: dict) -> dict:
    """Rank predicted view candidates, preserving a bounded return reserve."""
    if not isinstance(spec, dict) or spec.get("execution_mode") != "fixture_only":
        raise ValueError("only fixture_only prediction specs are accepted")
    task = spec.get("slot_id")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("nonempty required slot_id is needed")
    time_budget = _number(spec.get("remaining_time_s"), "remaining_time_s", low=0.001)
    buffer = _number(spec.get("return_buffer_s"), "return_buffer_s")
    if buffer >= time_budget:
        raise ValueError("return buffer must be smaller than budget")
    limits = spec.get("quality_policy")
    if not isinstance(limits, dict):
        raise ValueError("quality_policy object required")
    glare_cap = _number(limits.get("max_predicted_glare_fraction"), "max_predicted_glare_fraction", high=1)
    min_valid = _number(limits.get("min_predicted_valid_roi_fraction"), "min_predicted_valid_roi_fraction", high=1)
    w = spec.get("weights")
    if not isinstance(w, dict):
        raise ValueError("weights object required")
    glare_weight = _number(w.get("glare_penalty"), "glare_penalty")
    time_weight = _number(w.get("time_penalty"), "time_penalty")
    options = spec.get("candidates")
    if not isinstance(options, list) or not options:
        raise ValueError("candidates must be a nonempty list")

    ids = set()
    ranked = []
    diagnostics = []
    for item in options:
        if not isinstance(item, dict):
            raise ValueError("candidate must be object")
        key = item.get("pose_id")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("pose_id missing")
        if key in ids:
            raise ValueError("duplicate candidate pose_id")
        ids.add(key)
        for field in ("visibility_proxy_ok", "support_proxy_ok", "collision_proxy_ok"):
            _boolean(item.get(field), field)
        glare = _number(item.get("predicted_glare_fraction"), "predicted_glare_fraction", high=1)
        valid = _number(item.get("predicted_valid_roi_fraction"), "predicted_valid_roi_fraction", high=1)
        outbound = _number(item.get("outbound_s"), "outbound_s")
        capture = _number(item.get("capture_s"), "capture_s")
        home = _number(item.get("return_s"), "return_s")
        total = outbound + capture + home + buffer
        reasons = []
        if not item["visibility_proxy_ok"]:
            reasons.append("visibility_not_predicted")
        if not item["support_proxy_ok"]:
            reasons.append("support_proxy_reject")
        if not item["collision_proxy_ok"]:
            reasons.append("collision_proxy_reject")
        if glare > glare_cap:
            reasons.append("predicted_specular_glare")
        if valid < min_valid:
            reasons.append("insufficient_predicted_valid_roi")
        if total > time_budget:
            reasons.append("return_time_budget_exceeded")
        score = round(valid - glare_weight * glare - time_weight * total / time_budget, 9)
        diagnostics.append({
            "pose_id": key, "predicted_score": score,
            "estimated_total_with_buffer_s": total,
            "reason_codes": reasons,
        })
        if not reasons:
            ranked.append((score, key))
    ranked.sort(key=lambda p: (-p[0], p[1]))
    return {
        "slot_id": task,
        "status": "candidate_selected" if ranked else "no_feasible_candidate",
        "selected_pose_id": ranked[0][1] if ranked else None,
        "candidate_diagnostics": diagnostics,
        "ranking_kind": "declared_heuristic_on_supplied_predictions",
        "evidence_class": "software_fixture_only",
        "certifies_robot_safety": False,
        "observed_image_quality": None,
    }
