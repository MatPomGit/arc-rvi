"""Offline waypoint-level collision proxy diagnostics; never certifies motion."""

from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite, sqrt
from pathlib import Path

from .collision import inspect_collision_proxies

MAX_WAYPOINTS = 32
MAX_TRAJECTORY_BYTES = 65_536


def _no_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite trajectory JSON value: {value}")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate trajectory JSON field: {key}")
        result[key] = value
    return result


def load_trajectory(path: Path) -> tuple[dict, str]:
    """Load bounded, immutable local joint-state waypoints with SHA-256."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("trajectory must be a regular local non-symlinked file")
    if source.stat().st_size > MAX_TRAJECTORY_BYTES:
        raise ValueError("trajectory exceeds size limit")
    raw = source.read_bytes()
    if len(raw) > MAX_TRAJECTORY_BYTES:
        raise ValueError("trajectory exceeds size limit")
    try:
        data = json.loads(raw.decode("utf-8"), parse_constant=_no_nonfinite,
                          object_pairs_hook=_no_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid trajectory UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("trajectory must be a JSON object")
    return data, sha256(raw).hexdigest()


def validate_waypoints(spec: dict) -> list[dict]:
    """Validate the time-indexed JSON structure, not physical trajectories."""
    if (not isinstance(spec, dict)
            or set(spec) != {"schema_version", "waypoints"}
            or spec["schema_version"] != "1.0.0"):
        raise ValueError("unsupported trajectory schema")
    waypoints = spec["waypoints"]
    if not isinstance(waypoints, list) or not 2 <= len(waypoints) <= MAX_WAYPOINTS:
        raise ValueError("trajectory must have 2–32 waypoints")
    previous = -1.0
    for item in waypoints:
        if not isinstance(item, dict) or set(item) != {"time_s", "joint_positions"}:
            raise ValueError("invalid trajectory waypoint fields")
        time = item["time_s"]
        if isinstance(time, bool) or not isinstance(time, (int, float)):
            raise ValueError("waypoint time must be numeric")
        try:
            time = float(time)
        except (ValueError, OverflowError) as exc:
            raise ValueError("waypoint time outside numeric range") from exc
        if not isfinite(time) or time < 0 or time <= previous:
            raise ValueError("waypoint time must be finite and strictly increasing")
        previous = time
        if not isinstance(item["joint_positions"], dict):
            raise ValueError("waypoint joint_positions must be an object")
    return waypoints


def _chord_intersects_padded_box(
    start: list[float], stop: list[float],
    minimum: list[float], maximum: list[float], padding: float,
) -> bool:
    """Slab intersection of the centre chord and sphere-inflated AABB.

    The padded box is deliberately conservative near corners. A chord
    is *not* the generally curved FK trajectory between joint states.
    """
    left, right = 0.0, 1.0
    for i in range(3):
        lower, upper = minimum[i] - padding, maximum[i] + padding
        delta = stop[i] - start[i]
        if not all(isfinite(x) for x in (lower, upper, delta)):
            raise ValueError("expanded collision box exceeds finite numeric range")
        if delta == 0.0:
            if start[i] < lower or start[i] > upper:
                return False
            continue
        first, second = (lower - start[i]) / delta, (upper - start[i]) / delta
        if not all(isfinite(x) for x in (first, second)):
            raise ValueError("collision chord parameter exceeds finite range")
        left = max(left, min(first, second))
        right = min(right, max(first, second))
        if left > right:
            return False
    return True


def _joint_segment_kind(first: dict, second: dict) -> str:
    """Only unchanged rotary joints allow affine, fixed-base FK proxy centres."""
    kinds = first.get("movable_joint_types")
    next_kinds = second.get("movable_joint_types")
    initial = first.get("joints")
    final = second.get("joints")
    if (not isinstance(kinds, dict) or not kinds
            or kinds != next_kinds or not isinstance(initial, dict)
            or not isinstance(final, dict) or set(initial) != set(kinds)
            or set(final) != set(kinds)):
        raise ValueError("inconsistent FK joint types or state between waypoints")
    if any(kind not in ("revolute", "continuous", "prismatic")
           for kind in kinds.values()):
        raise ValueError("unsupported joint kind for segmented proxy analysis")
    if any(initial[name] != final[name]
           for name, kind in kinds.items() if kind != "prismatic"):
        return "rotary_motion_unresolved"
    return "affine_prismatic_interpolation"


def _relative_centre_segment_clearance(
    first: list[float], second: list[float], radius_sum: float,
) -> float:
    """Minimum signed gap for linearly moving sphere centres, independently of time."""
    delta = [b - a for a, b in zip(first, second)]
    length_sq = sum(v * v for v in delta)
    if not isfinite(length_sq):
        raise ValueError("self-sweep delta exceeds finite range")
    parameter = (max(0.0, min(1.0, -sum(a * d for a, d in zip(first, delta))
                                / length_sq)) if length_sq > 0 else 0.0)
    distance_sq = sum((a + parameter * d) ** 2
                      for a, d in zip(first, delta))
    result = sqrt(distance_sq) - radius_sum
    if not isfinite(result):
        raise ValueError("self-sweep clearance exceeds finite range")
    return result


def inspect_waypoint_collision(poses: list[dict], fixture: dict,
                               waypoint_times: list[float]) -> dict:
    """Screen waypoint FK proxies and a narrow affine-translation sweep.

    When every revolute/continuous joint is unchanged, linearly interpolated
    prismatic joint positions yield exactly affine centres for link spheres.
    This does NOT establish continuous collision safety for the full robot.
    """
    if not isinstance(poses, list) or not 2 <= len(poses) <= MAX_WAYPOINTS:
        raise ValueError("invalid number of configured poses")
    if (not isinstance(waypoint_times, list)
            or len(waypoint_times) != len(poses)):
        raise ValueError("configured pose / waypoint count mismatch")
    evaluations = [inspect_collision_proxies(pose, fixture) for pose in poses]
    ids = set(evaluations[0]["sphere_centres_world_m"])
    if any(set(item["sphere_centres_world_m"]) != ids for item in evaluations):
        raise ValueError("sphere IDs must be identical across all poses")

    boxes = {item["id"]: (item["min_xyz_m"], item["max_xyz_m"])
             for item in fixture["boxes"]}
    radii = {item["id"]: item["radius_m"] for item in fixture["spheres"]}
    margin = fixture["clearance_margin_m"]
    possible = []
    possible_self = []
    segment_kinds = []
    for index, (first, second) in enumerate(zip(evaluations, evaluations[1:])):
        kind = _joint_segment_kind(poses[index], poses[index + 1])
        segment_kinds.append(kind)
        for sid in sorted(ids):
            start = first["sphere_centres_world_m"][sid]
            stop = second["sphere_centres_world_m"][sid]
            for bid in sorted(boxes):
                lo, hi = boxes[bid]
                if _chord_intersects_padded_box(
                        start, stop, lo, hi, radii[sid] + margin):
                    possible.append({
                        "segment_index": index,
                        "start_time_s": waypoint_times[index],
                        "end_time_s": waypoint_times[index + 1],
                        "sphere_id": sid,
                        "obstacle_id": bid,
                        "status": "possible_chord_obstacle_overlap",
                    })
        if kind == "affine_prismatic_interpolation":
            for pair in fixture["self_pairs"]:
                left, right = sorted(pair)
                centre_a = first["sphere_centres_world_m"]
                centre_b = second["sphere_centres_world_m"]
                start = [centre_a[left][i] - centre_a[right][i] for i in range(3)]
                end = [centre_b[left][i] - centre_b[right][i] for i in range(3)]
                clearance = _relative_centre_segment_clearance(
                    start, end, radii[left] + radii[right] + margin)
                if clearance <= 0:
                    possible_self.append({
                        "segment_index": index,
                        "start_time_s": waypoint_times[index],
                        "end_time_s": waypoint_times[index + 1],
                        "first_sphere_id": left,
                        "second_sphere_id": right,
                        "minimum_signed_clearance_m": clearance,
                        "status": "affine_self_proxy_overlap_candidate",
                    })

    collisions = [i for i, item in enumerate(evaluations)
                  if item["status"] == "proxy_overlap_detected"]
    if collisions:
        status = "proxy_overlap_at_waypoint"
    elif possible:
        status = "possible_chord_obstacle_overlap"
    elif possible_self:
        status = "affine_self_proxy_overlap_candidate"
    elif "rotary_motion_unresolved" in segment_kinds:
        status = "rotational_sweep_unresolved"
    else:
        status = "affine_proxy_sweep_clear_unverified_body"
    return {
        "schema_version": "1.0.0",
        "evidence_type": "synthetic_fixture",
        "model": "sampled_fk_static_proxy_with_chord_screen_v1",
        "status": status,
        "waypoint_count": len(poses),
        "segment_count": len(poses) - 1,
        "waypoint_times_s": waypoint_times,
        "overlap_waypoint_indices": collisions,
        "possible_chord_contacts": possible,
        "possible_affine_self_contacts": possible_self,
        "segment_kinematics": segment_kinds,
        "affine_proxy_segments": segment_kinds.count("affine_prismatic_interpolation"),
        "rotationally_unresolved_segments": segment_kinds.count("rotary_motion_unresolved"),
        "checked_static_proxy_pairs": sum(v["checked_pairs"] for v in evaluations),
        "waypoint_proxy_statuses": [v["status"] for v in evaluations],
        "continuous_articulated_collision_validation": "not_performed",
        "inter_sample_joint_motion": "affine_prismatic_only_or_unresolved_rotation",
        "self_collision_between_waypoints": "explicit_pairs_affine_only",
        "support_and_dynamics": "not_evaluated",
        "full_body_collision_validation": "not_performed",
        "robot_adapter": "not_configured",
    }
