"""Fixture-only sphere/AABB collision proxies for already-audited URDF FK poses.

These checks never certify whole-body collision clearance or motion safety.
"""

from __future__ import annotations

from hashlib import sha256
import json
from math import dist, hypot, isfinite
from pathlib import Path

MAX_FIXTURE_BYTES = 65_536
MAX_PROXIES = 32
MAX_BOXES = 32
MAX_SELF_PAIRS = 64


def _number(value: object, context: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context} must be a finite number")
    try:
        x = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{context} exceeds numeric range") from exc
    if not isfinite(x) or (positive and x <= 0):
        raise ValueError(f"{context} must be finite and valid")
    return x


def _point3(value: object, context: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{context} must have three coordinates")
    return tuple(_number(v, context) for v in value)


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError(f"{context} must be a nonempty bounded identifier")
    return value


def load_collision_fixture(path: Path) -> tuple[dict, str]:
    """Read bounded local JSON; do not follow a symlink or contact hardware."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("collision fixture must be a regular non-symlinked local file")
    if source.stat().st_size > MAX_FIXTURE_BYTES:
        raise ValueError("collision fixture exceeds size limit")
    raw = source.read_bytes()
    if len(raw) > MAX_FIXTURE_BYTES:
        raise ValueError("collision fixture exceeds size limit")
    try:
        payload = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid collision fixture JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("collision fixture must be a JSON object")
    return payload, sha256(raw).hexdigest()


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite collision fixture JSON constant: {value}")


def _audit_urdf_primitive_envelopes(
    frames: dict, declared: dict, margin: float, metadata: object,
) -> dict:
    """Assess containment of *ideal URDF primitives*, not physical meshes.

    A separate declared sphere must enclose each primitive's conservative
    circumsphere in the same link-local coordinate frame. This deliberately
    rejects cases where a union of spheres might suffice but is unproved.
    """
    if metadata is None:
        return {"status": "urdf_collision_reference_unavailable",
                "actual_link_collision_volume_validation": "not_performed"}
    if (not isinstance(metadata, dict)
            or set(metadata) != {"source_sha256", "status", "by_link"}
            or metadata["status"] != "offline_urdf_primitive_reference_only"
            or not isinstance(metadata["by_link"], dict)
            or set(metadata["by_link"]) != set(frames)):
        raise ValueError("invalid pinned URDF collision-reference metadata")
    checks = []
    missing_reference = []
    unverified = 0
    enclosed = 0
    by_link = metadata["by_link"]
    for link in sorted(frames):
        entries = by_link[link]
        if not isinstance(entries, list):
            raise ValueError("invalid URDF collision-reference entries")
        if not entries:
            missing_reference.append(link)
        local_spheres = [
            (_point3(item["center_local_m"], "declared local proxy centre"),
             _number(item["radius_m"], "declared radius", positive=True))
            for item in declared if item["link"] == link
        ]
        for item in entries:
            if not isinstance(item, dict) or set(item) != {
                    "id", "status", "primitive_kind",
                    "bounding_sphere_centre_local_m",
                    "bounding_sphere_radius_m"}:
                raise ValueError("invalid URDF collision primitive entry")
            status = "unverified_reference_geometry"
            best = None
            if item["status"] == "analytic_primitive_bound":
                centre = _point3(item["bounding_sphere_centre_local_m"],
                                 "URDF primitive enclosing centre")
                radius = _number(item["bounding_sphere_radius_m"],
                                 "URDF primitive enclosing radius",
                                 positive=True)
                for proxy_centre, proxy_radius in local_spheres:
                    remaining = proxy_radius - (dist(proxy_centre, centre)
                                                + radius + margin)
                    if not isfinite(remaining):
                        raise ValueError("non-finite primitive-envelope clearance")
                    best = remaining if best is None else max(best, remaining)
                if best is None:
                    status = "missing_declared_link_proxy"
                else:
                    # Strict positive margin, not a claim of certified
                    # floating-point interval enclosure near tangency.
                    guard = 1e-9 + 1e-12 * max(radius, abs(best), 1.0)
                    status = ("circumsphere_enclosed_by_declared_proxy"
                              if best > guard else
                              "primitive_enclosure_not_demonstrated")
            elif item["status"] != "unverified_geometry":
                raise ValueError("invalid collision primitive reference status")
            if status == "circumsphere_enclosed_by_declared_proxy":
                enclosed += 1
            else:
                unverified += 1
            checks.append({
                "primitive_id": item["id"],
                "link": link,
                "primitive_kind": item["primitive_kind"],
                "status": status,
                "best_signed_enclosing_margin_m": best,
            })
    return {
        "status": (
            "declared_urdf_primitives_enclosed_unverified_robot"
            if checks and not unverified and not missing_reference else
            "incomplete_or_unverified_reference_coverage"
        ),
        "urdf_source_sha256": metadata["source_sha256"],
        "primitive_collision_elements": len(checks),
        "enclosed_primitive_bounds": enclosed,
        "not_demonstrated_or_unknown": unverified,
        "links_without_urdf_collision_reference": missing_reference,
        "primitive_checks": checks,
        "reference_scope": "ideal_urdf_sphere_box_cylinder_only",
        "mesh_files_loaded": False,
        "actual_link_collision_volume_validation": "not_performed",
        "full_body_collision_validation": "not_performed",
    }


def inspect_collision_proxies(configured_pose: dict, fixture: dict) -> dict:
    """Report only explicit spheres/boxes/pairs at one static FK configuration.

    A clear *proxy* result never means a full robot, the unsampled link
    volumes, the connecting motion trajectory, or the real site is clear.
    """
    if (not isinstance(configured_pose, dict)
            or configured_pose.get("status") != "offline_articulated_fk_only"):
        raise ValueError("collision proxies require configured offline URDF FK")
    frames = configured_pose.get("frame_poses")
    if not isinstance(frames, dict) or not frames:
        raise ValueError("FK frames missing")
    if not isinstance(fixture, dict) or set(fixture) != {
            "schema_version", "spheres", "boxes", "self_pairs",
            "clearance_margin_m"}:
        raise ValueError("collision fixture has invalid schema fields")
    if fixture["schema_version"] != "1.0.0":
        raise ValueError("unsupported collision fixture version")
    margin = _number(fixture["clearance_margin_m"], "clearance margin")
    if margin < 0:
        raise ValueError("clearance margin must not be negative")
    spheres = fixture["spheres"]
    boxes = fixture["boxes"]
    pairs = fixture["self_pairs"]
    if not isinstance(spheres, list) or not 1 <= len(spheres) <= MAX_PROXIES:
        raise ValueError("collision spheres must contain 1–32 items")
    if not isinstance(boxes, list) or len(boxes) > MAX_BOXES:
        raise ValueError("collision boxes must contain at most 32 items")
    if not isinstance(pairs, list) or len(pairs) > MAX_SELF_PAIRS:
        raise ValueError("explicit self-pairs must contain at most 64 pairs")
    if not boxes and not pairs:
        raise ValueError("at least one obstacle box or explicit self-pair is required")

    sphere_centres = {}
    sphere_radii = {}
    sphere_links = {}
    for entry in spheres:
        if not isinstance(entry, dict) or set(entry) != {
                "id", "link", "center_local_m", "radius_m"}:
            raise ValueError("invalid sphere fields")
        sid = _text(entry["id"], "sphere id")
        link = _text(entry["link"], "URDF link")
        if sid in sphere_centres:
            raise ValueError("duplicate sphere id")
        if link not in frames:
            raise ValueError(f"undeclared collision link: {link}")
        local = _point3(entry["center_local_m"], "local sphere centre")
        radius = _number(entry["radius_m"], "sphere radius", positive=True)
        frame = frames[link]
        position = _point3(frame["translation_m"], "FK frame position")
        rotation = frame["rotation_matrix"]
        if (not isinstance(rotation, list) or len(rotation) != 3
                or any(not isinstance(row, list) or len(row) != 3
                       for row in rotation)):
            raise ValueError("FK rotation matrix has invalid shape")
        rot = tuple(tuple(_number(v, "FK rotation") for v in row)
                    for row in rotation)
        centre = tuple(position[i] + sum(rot[i][j] * local[j] for j in range(3))
                       for i in range(3))
        if not all(isfinite(v) for v in centre):
            raise ValueError("transformed collision sphere centre exceeds numeric range")
        sphere_centres[sid] = centre
        sphere_radii[sid] = radius
        sphere_links[sid] = link

    obstacles = {}
    for entry in boxes:
        if not isinstance(entry, dict) or set(entry) != {
                "id", "min_xyz_m", "max_xyz_m"}:
            raise ValueError("invalid axis-aligned box fields")
        bid = _text(entry["id"], "obstacle id")
        if bid in obstacles:
            raise ValueError("duplicate obstacle id")
        lo = _point3(entry["min_xyz_m"], "AABB minimum")
        hi = _point3(entry["max_xyz_m"], "AABB maximum")
        if any(a >= b for a, b in zip(lo, hi)):
            raise ValueError("axis-aligned box must have positive 3D extents")
        obstacles[bid] = lo, hi

    self_pairs = []
    seen_pairs = set()
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("self-pair must contain two sphere ids")
        first = _text(pair[0], "self sphere id")
        second = _text(pair[1], "self sphere id")
        if first not in sphere_centres or second not in sphere_centres or first == second:
            raise ValueError("self-pair references missing or identical spheres")
        key = tuple(sorted((first, second)))
        if key in seen_pairs:
            raise ValueError("duplicate self-pair")
        seen_pairs.add(key)
        self_pairs.append(key)

    # Presence of a declared sphere for a URDF link is not evidence of
    # complete collision volume for that link. Missing links and omitted
    # cross-link self-pairs must remain explicit even when observed checks
    # report non-overlap.
    represented_links = sorted(set(sphere_links.values()))
    missing_links = sorted(set(frames) - set(represented_links))
    unreviewed_pairs = [
        (first, second)
        for i, first in enumerate(sorted(sphere_links))
        for second in sorted(sphere_links)[i + 1:]
        if (sphere_links[first] != sphere_links[second]
            and (first, second) not in seen_pairs)
    ]
    checks = []
    for sid, centre in sorted(sphere_centres.items()):
        for bid, (lo, hi) in sorted(obstacles.items()):
            outside = tuple(max(lo[i] - centre[i], 0.0,
                                centre[i] - hi[i]) for i in range(3))
            clearance = hypot(*outside) - sphere_radii[sid] - margin
            if not isfinite(clearance):
                raise ValueError("collision proxy clearance is not finite")
            checks.append({
                "kind": "sphere_aabb", "first_id": sid, "second_id": bid,
                "signed_clearance_m": clearance, "touch_or_overlap": clearance <= 0,
            })
    for first, second in sorted(self_pairs):
        clearance = (dist(sphere_centres[first], sphere_centres[second])
                     - sphere_radii[first] - sphere_radii[second] - margin)
        if not isfinite(clearance):
            raise ValueError("self proxy clearance is not finite")
        checks.append({
            "kind": "explicit_self_pair", "first_id": first, "second_id": second,
            "signed_clearance_m": clearance, "touch_or_overlap": clearance <= 0,
        })
    return {
        "schema_version": "1.0.0",
        "evidence_type": "synthetic_fixture",
        "status": ("proxy_overlap_detected" if any(x["touch_or_overlap"] for x in checks)
                   else "no_proxy_overlap_unverified"),
        "checked_pairs": len(checks),
        "proxy_spheres": len(spheres),
        "urdf_primitive_envelope_audit": _audit_urdf_primitive_envelopes(
            frames, spheres, margin, configured_pose.get("urdf_collision_geometry")),
        "declared_link_presence_audit": {
            "urdf_link_count": len(frames),
            "links_with_proxy_spheres": represented_links,
            "links_without_proxy_spheres": missing_links,
            "all_declared_links_have_proxy": not missing_links,
            "unreviewed_cross_link_self_pair_count": len(unreviewed_pairs),
            "unreviewed_cross_link_self_pair_examples": [
                list(pair) for pair in unreviewed_pairs[:16]
            ],
            "actual_link_collision_volume_validation": "not_performed",
            "adjacent_joint_contact_exemption_review": "not_performed",
        },
        "sphere_centres_world_m": {
            identifier: list(point)
            for identifier, point in sorted(sphere_centres.items())
        },
        "obstacle_boxes": len(boxes),
        "explicit_self_pairs": len(self_pairs),
        "clearance_margin_m": margin,
        "minimum_signed_clearance_m": min(x["signed_clearance_m"] for x in checks),
        "checks": checks,
        "full_body_collision_validation": "not_performed",
        "trajectory_sweep_validation": "not_performed",
        "robot_adapter": "not_configured",
    }
