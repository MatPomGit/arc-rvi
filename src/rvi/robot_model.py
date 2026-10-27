"""Offline checks for versioned articulated robot descriptions; never drives hardware."""

from __future__ import annotations

from collections import Counter, deque
from hashlib import sha256
from math import cos, isfinite, sin, sqrt
from pathlib import Path
import xml.etree.ElementTree as ET

MAX_URDF_BYTES = 2_000_000
JOINT_TYPES = {"fixed", "revolute", "continuous", "prismatic", "floating"}


def _vector(text: str, size: int, context: str) -> tuple[float, ...]:
    try:
        parts = text.split()
        if len(parts) != size:
            raise ValueError("wrong number of coordinates")
        values = tuple(float(part) for part in parts)
        if not all(isfinite(value) for value in values):
            raise ValueError("non-finite coordinate")
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"invalid {context}") from exc
    return values


def _rotation(rpy: tuple[float, ...]) -> tuple[tuple[float, ...], ...]:
    """URDF fixed-axis roll, pitch, yaw: Rz(yaw) Ry(pitch) Rx(roll)."""
    roll, pitch, yaw = rpy
    cr, sr = cos(roll), sin(roll)
    cp, sp = cos(pitch), sin(pitch)
    cy, sy = cos(yaw), sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp, cp * sr, cp * cr),
    )


IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _multiply(a: tuple, b: tuple) -> tuple:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3))
                       for j in range(3)) for i in range(3))


def _apply(matrix: tuple, vector: tuple) -> tuple:
    return tuple(sum(matrix[i][j] * vector[j] for j in range(3))
                 for i in range(3))


def inspect_urdf(
    path: Path, expected_sha256: str, *, camera_frame: str | None = None,
) -> dict:
    """Validate joint graph/limits and calculate zero-joint frame transforms.

    No mesh geometry, dynamic movement, inverse kinematics, collision, sensor
    calibration, hardware identity, or physical safety is certified.
    """
    if (not isinstance(expected_sha256, str)
            or len(expected_sha256) != 64
            or any(char not in "0123456789abcdef" for char in expected_sha256)):
        raise ValueError("expected_sha256 must be 64 lowercase hex digits")
    if camera_frame is not None and (
            not isinstance(camera_frame, str) or not camera_frame.strip()):
        raise ValueError("camera_frame must be a nonempty link name")
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("URDF must be a regular, non-symlinked local file")
    if source.stat().st_size > MAX_URDF_BYTES:
        raise ValueError("URDF exceeds offline input size limit")
    raw = source.read_bytes()
    if len(raw) > MAX_URDF_BYTES:
        raise ValueError("URDF exceeds offline input size limit")
    digest = sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("URDF SHA-256 does not match pinned expected bytes")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("URDF DTD and entities are not accepted")
    try:
        xml = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("malformed URDF XML") from exc
    if xml.tag != "robot" or not xml.get("name", "").strip():
        raise ValueError("URDF needs a named robot root")

    links = [entry.get("name", "") for entry in xml.findall("link")]
    if not links or any(not link.strip() for link in links):
        raise ValueError("URDF contains missing link names")
    if len(links) != len(set(links)):
        raise ValueError("duplicate URDF links")
    known = set(links)
    by_parent: dict[str, list[tuple]] = {name: [] for name in links}
    child_parent: dict[str, str] = {}
    joint_names = set()
    types = Counter()
    neutral_outside = []
    floating_parents = []
    for joint in xml.findall("joint"):
        identifier, kind = joint.get("name", ""), joint.get("type")
        if not identifier.strip() or identifier in joint_names or kind not in JOINT_TYPES:
            raise ValueError("invalid, duplicate or unsupported URDF joint")
        joint_names.add(identifier)
        types[kind] += 1
        parent_element, child_element = joint.find("parent"), joint.find("child")
        if parent_element is None or child_element is None:
            raise ValueError("joint needs parent and child links")
        parent, child = parent_element.get("link"), child_element.get("link")
        if (parent not in known or child not in known or parent == child
                or child in child_parent):
            raise ValueError("unknown, self-linked or multiply parented link")
        child_parent[child] = parent
        if kind == "floating":
            floating_parents.append(parent)
        origin = joint.find("origin")
        xyz = _vector(origin.get("xyz", "0 0 0") if origin is not None else "0 0 0",
                      3, "joint xyz in metres")
        rpy = _vector(origin.get("rpy", "0 0 0") if origin is not None else "0 0 0",
                      3, "joint roll/pitch/yaw in radians")
        if kind not in ("fixed", "floating"):
            axis = joint.find("axis")
            v = _vector(axis.get("xyz", "1 0 0") if axis is not None else "1 0 0",
                        3, "joint axis")
            if sqrt(sum(x * x for x in v)) < 1e-12:
                raise ValueError("joint axis cannot be zero")
        if kind in ("revolute", "prismatic"):
            limit = joint.find("limit")
            if limit is None:
                raise ValueError("bounded joint has no limits")
            lower = _vector(limit.get("lower", ""), 1, "joint lower limit")[0]
            upper = _vector(limit.get("upper", ""), 1, "joint upper limit")[0]
            if lower > upper:
                raise ValueError("joint lower limit exceeds upper limit")
            if not lower <= 0 <= upper:
                neutral_outside.append(identifier)
        by_parent[parent].append((child, xyz, _rotation(rpy)))

    roots = known - set(child_parent)
    if len(roots) != 1 or len(joint_names) != len(links) - 1:
        raise ValueError("URDF joints must form exactly one rooted tree")
    root = next(iter(roots))
    if len(floating_parents) > 1 or any(parent != root for parent in floating_parents):
        raise ValueError("only one virtual floating-base joint at the root is supported")
    poses: dict[str, tuple] = {root: (IDENTITY, (0.0, 0.0, 0.0))}
    depth = {root: 0}
    queue = deque([root])
    while queue:
        parent = queue.popleft()
        rotation, position = poses[parent]
        for child, xyz, origin_rotation in by_parent[parent]:
            translated = _apply(rotation, xyz)
            child_xyz = tuple(position[i] + translated[i] for i in range(3))
            poses[child] = (_multiply(rotation, origin_rotation), child_xyz)
            depth[child] = depth[parent] + 1
            queue.append(child)
    if len(poses) != len(links):
        raise ValueError("disconnected or cyclic URDF joint graph")

    camera = {"requested_frame": camera_frame, "frame_in_model": False,
              "zero_joint_pose": None}
    if camera_frame in poses:
        rotation, xyz = poses[camera_frame]
        camera["frame_in_model"] = True
        camera["zero_joint_pose"] = {
            "translation_m": list(xyz),
            "rotation_matrix": [list(row) for row in rotation],
            "relative_to": root,
        }
    return {
        "schema_version": "1.0.0", "evidence_type": "fixture",
        "status": "offline_description_structure_only",
        "robot_name": xml.get("name"), "source_sha256": digest,
        "root_link": root, "link_count": len(links),
        "joint_count": len(joint_names), "joint_types": dict(sorted(types.items())),
        "max_tree_depth": max(depth.values()),
        "floating_base_zero_pose_assumed": bool(floating_parents),
        "zero_joint_pose_within_declared_limits": not neutral_outside,
        "zero_pose_limit_violations": sorted(neutral_outside),
        "camera_frame": camera,
        "physical_or_collision_validation": "not_performed",
        "robot_adapter": "not_configured",
    }
