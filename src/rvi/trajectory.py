"""Offline waypoint-level collision proxy diagnostics; never certifies motion."""

from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite, sqrt, ulp
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


MAX_ROTARY_EVALUATIONS = 64
# Conservative software arithmetic envelope, NOT a physical robot range.
MAX_ROTARY_NUMERIC_LENGTH_M = 1_000_000.0
MAX_ROTARY_NUMERIC_ANGLE_RAD = 100.0


def _conservative_centre_speed(first: dict, last: dict,
                               fixture: dict) -> tuple[float, float]:
    """Global derivative bound in metres per unit interpolation parameter.

    All URDF origin lengths upper-bound the length of any ancestor-to-point
    chain. Adding absolute prismatic offsets and local sphere offsets
    bounds the radius from any rotating joint axis to a declared proxy
    centre. This deliberately over-approximates even unrelated joints.
    """
    base = first.get("all_joint_origin_length_sum_m")
    if (isinstance(base, bool) or not isinstance(base, (int, float))
            or not isfinite(base) or base < 0
            or base != last.get("all_joint_origin_length_sum_m")):
        raise ValueError("rotary proxy motion has no trusted finite URDF origin bound")
    kinds = first["movable_joint_types"]
    start, stop = first["joints"], last["joints"]
    # Reject extreme scales rather than interpret rounded clearances as proof.
    # This includes declared obstacles: their world-coordinate magnitude
    # contributes to floating-point uncertainty even for a small robot.
    try:
        coordinates = [
            abs(component)
            for sphere in fixture["spheres"]
            for component in sphere["center_local_m"]
        ] + [
            abs(component)
            for obstacle in fixture["boxes"]
            for key in ("min_xyz_m", "max_xyz_m")
            for component in obstacle[key]
        ]
        for pose in (first, last):
            coordinates.extend(
                abs(component)
                for frame in pose["frame_poses"].values()
                for component in frame["translation_m"])
        model_scale = max([1.0, base, *coordinates])
        if (not isfinite(model_scale)
                or model_scale > MAX_ROTARY_NUMERIC_LENGTH_M):
            raise ValueError("rotary geometry exceeds audited numeric scale")
        if any(abs(value) > (MAX_ROTARY_NUMERIC_ANGLE_RAD
                            if kinds[name] in ("revolute", "continuous")
                            else MAX_ROTARY_NUMERIC_LENGTH_M)
               for name in kinds for value in (start[name], stop[name])):
            raise ValueError("rotary joint coordinate exceeds audited numeric scale")
    except (KeyError, TypeError, OverflowError) as exc:
        raise ValueError("rotary numeric bound metadata invalid") from exc
    try:
        prismatic_extent = sum(max(abs(start[name]), abs(stop[name]))
                              for name in kinds if kinds[name] == "prismatic")
        angular_travel = sum(abs(stop[name] - start[name])
                             for name in kinds if kinds[name] in (
                                 "revolute", "continuous"))
        linear_travel = sum(abs(stop[name] - start[name])
                            for name in kinds if kinds[name] == "prismatic")
        local_extent = max(
            sqrt(sum(component * component for component in sphere["center_local_m"]))
            for sphere in fixture["spheres"])
        radius_bound = base + prismatic_extent + local_extent
        speed = angular_travel * radius_bound + linear_travel
    except (OverflowError, ValueError) as exc:
        raise ValueError("rotary proxy bound could not be computed") from exc
    if not all(isfinite(value) for value in (
            prismatic_extent, angular_travel, linear_travel,
            local_extent, radius_bound, speed)):
        raise ValueError("rotary proxy bound exceeds numeric validity")
    if (radius_bound > MAX_ROTARY_NUMERIC_LENGTH_M
            or angular_travel > MAX_ROTARY_NUMERIC_ANGLE_RAD
            or linear_travel > MAX_ROTARY_NUMERIC_LENGTH_M):
        raise ValueError("rotary interpolation exceeds audited numeric domain")
    # A deliberately large error allowance for chained matrix operations,
    # coordinate differences and distance evaluation (not formal interval
    # arithmetic). Outside this measured software domain we fail closed.
    error_guard = 1e-9 + 64.0 * (len(kinds) + 1) * ulp(
        max(model_scale, radius_bound, 1.0))
    if not isfinite(error_guard):
        raise ValueError("rotary arithmetic guard is not finite")
    return speed, error_guard


def _linear_joint_state(first: dict, second: dict, fraction: float) -> dict:
    """Declare linear interpolation in joint coordinates, not controller motion."""
    state = {}
    for name in first["joints"]:
        a, b = first["joints"][name], second["joints"][name]
        value = a * (1.0 - fraction) + b * fraction
        if not isfinite(value):
            raise ValueError("interpolated joint position is not finite")
        state[name] = value
    return state


def inspect_rotary_proxy_sweep(
    poses: list[dict], fixture: dict, pose_at,
    *, max_evaluations: int = MAX_ROTARY_EVALUATIONS,
) -> dict:
    """Bound static declared sphere-proxy contact over interpolated joints.

    Under fixed-base linear joint interpolation, a global per-proxy centre
    Lipschitz bound safely excludes collision if every declared contact
    clearance is larger than the bound throughout a subinterval. Between-
    waypoint FK samples expose counterexamples; budget exhaustion is UNKNOWN.
    This is never proof for omitted robot geometry, dynamics or true motion.
    """
    if (isinstance(max_evaluations, bool)
            or not isinstance(max_evaluations, int)
            or not 0 <= max_evaluations <= 128):
        raise ValueError("rotary evaluation limit must be an integer from 0 to 128")
    if not isinstance(poses, list) or not 2 <= len(poses) <= MAX_WAYPOINTS:
        raise ValueError("rotary sweep requires 2–32 FK waypoints")
    budget_used = 0
    outcomes = []
    for index, (first, last) in enumerate(zip(poses, poses[1:])):
        if _joint_segment_kind(first, last) == "affine_prismatic_interpolation":
            outcomes.append({"segment_index": index, "status": "affine_handled_separately",
                             "evaluations": 0, "collision_fraction": None,
                             "unresolved_intervals": 0})
            continue

        try:
            speed, rounding_guard = _conservative_centre_speed(first, last, fixture)
        except ValueError:
            outcomes.append({"segment_index": index, "status": "unresolved_invalid_bound",
                             "evaluations": 0, "collision_fraction": None,
                             "unresolved_intervals": 1})
            continue

        # A small positive rounding allowance prevents classifying a
        # numerical near-contact as geometrically proven clear.
        epsilon = rounding_guard + 1e-12 * speed
        queue = [(0.0, 1.0, first)]
        unresolved = 0
        collision_fraction = None
        visited = 0
        while queue:
            left, right, initial = queue.pop()
            static = inspect_collision_proxies(initial, fixture)
            if static["status"] == "proxy_overlap_detected":
                collision_fraction = left
                break
            width = right - left
            if not isfinite(width) or width <= 0:
                unresolved += 1
                continue
            safe = all(
                check["signed_clearance_m"] >
                speed * width * (2 if check["kind"] == "explicit_self_pair" else 1)
                + epsilon
                for check in static["checks"]
            )
            if safe:
                continue
            if budget_used >= max_evaluations:
                unresolved += 1 + len(queue)
                break
            middle = (left + right) / 2.0
            if middle == left or middle == right:
                unresolved += 1
                continue
            state = _linear_joint_state(first, last, middle)
            candidate = pose_at(state)
            # Validate that the supplied evaluator returns the requested
            # exact FK state; an untrusted/incompatible callback is rejected.
            if (not isinstance(candidate, dict)
                    or candidate.get("joints") != state
                    or candidate.get("movable_joint_types")
                    != first.get("movable_joint_types")
                    or candidate.get("all_joint_origin_length_sum_m")
                    != first.get("all_joint_origin_length_sum_m")):
                raise ValueError("intermediate FK state does not match requested joints")
            midpoint = inspect_collision_proxies(candidate, fixture)
            budget_used += 1
            visited += 1
            if midpoint["status"] == "proxy_overlap_detected":
                collision_fraction = middle
                break
            queue.append((middle, right, candidate))
            queue.append((left, middle, initial))

        if collision_fraction is not None:
            status = "proxy_overlap_between_waypoints"
        elif unresolved:
            status = "rotary_sweep_unresolved_budget"
        else:
            status = "rotary_declared_proxy_clear_only"
        outcomes.append({
            "segment_index": index,
            "status": status,
            "evaluations": visited,
            "collision_fraction": collision_fraction,
            "unresolved_intervals": unresolved,
        })

    if any(x["status"] == "proxy_overlap_between_waypoints" for x in outcomes):
        overall = "proxy_overlap_between_waypoints"
    elif any(x["status"].startswith(("unresolved_", "rotary_sweep_unresolved"))
             for x in outcomes):
        overall = "rotary_sweep_unresolved"
    else:
        overall = "declared_proxies_only_screened"
    return {
        "schema_version": "1.0.0",
        "model": "conservative_global_fk_centre_lipschitz_v1",
        "evidence_type": "synthetic_fixture",
        "status": overall,
        "total_evaluations": budget_used,
        "max_evaluations": max_evaluations,
        "numeric_model_limit_m": MAX_ROTARY_NUMERIC_LENGTH_M,
        "numeric_joint_angle_limit_rad": MAX_ROTARY_NUMERIC_ANGLE_RAD,
        "numeric_guard_type": "conservative_ulp_allowance_not_formal_interval_arithmetic",
        "segments": outcomes,
        "assumed_joint_motion": "linear_interpolation_fixed_virtual_base",
        "coverage": "declared_spheres_AABBs_and_explicit_self_pairs_only",
        "full_body_or_robot_motion_certification": "not_performed",
    }


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
