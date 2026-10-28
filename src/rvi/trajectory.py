"""Offline waypoint-level collision proxy diagnostics; never certifies motion."""

from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite
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


def inspect_waypoint_collision(poses: list[dict], fixture: dict,
                               waypoint_times: list[float]) -> dict:
    """Screen supplied FK snapshots and straight centre chords only.

    Every snapshot must already be derived from an independently validated
    URDF joint-state parser. No interpolation of actual robot joints or
    physical continuous collision validation is performed.
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
    for index, (first, second) in enumerate(zip(evaluations, evaluations[1:])):
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

    collisions = [i for i, item in enumerate(evaluations)
                  if item["status"] == "proxy_overlap_detected"]
    if collisions:
        status = "proxy_overlap_at_waypoint"
    elif possible:
        status = "possible_chord_obstacle_overlap"
    else:
        status = "sampled_proxy_clear_between_samples_unverified"
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
        "checked_static_proxy_pairs": sum(v["checked_pairs"] for v in evaluations),
        "waypoint_proxy_statuses": [v["status"] for v in evaluations],
        "continuous_articulated_collision_validation": "not_performed",
        "inter_sample_joint_motion": "not_reconstructed",
        "self_collision_between_waypoints": "not_evaluated",
        "support_and_dynamics": "not_evaluated",
        "full_body_collision_validation": "not_performed",
        "robot_adapter": "not_configured",
    }
