"""Synthetic static-foot support projection checks; no gait or robot hardware I/O."""

from __future__ import annotations

from hashlib import sha256
import json
from math import hypot, isfinite
from pathlib import Path

from .geometry import segment_distance

MAX_SPEC_BYTES = 65536
SUPPORTED_TERRAIN = "flat_horizontal"
TERRAIN_CLASSES = {SUPPORTED_TERRAIN, "steps", "slope", "loose", "unknown"}


def _number(value: object, name: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not isfinite(result) or (nonnegative and result < 0):
        raise ValueError(f"{name} must be finite and within domain")
    return result


def _point(value: object, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain two coordinates")
    return (_number(value[0], name), _number(value[1], name))


def _cross(a: tuple[float, float], b: tuple[float, float],
           c: tuple[float, float]) -> float:
    result = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if not isfinite(result):
        raise ValueError("geometry overflow")
    return result


def _validated_patch(value: object, index: int) -> tuple[list[tuple[float, float]], float, str]:
    if not isinstance(value, dict) or set(value) != {
            "id", "footprint_xy_m", "height_m", "contact_state"}:
        raise ValueError(f"contact {index} has invalid fields")
    name = value["id"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("contact id must be nonempty")
    state = value["contact_state"]
    if state not in ("assumed", "unknown"):
        raise ValueError("contact_state must be assumed or unknown")
    height = _number(value["height_m"], "height_m")
    vertices = value["footprint_xy_m"]
    if not isinstance(vertices, list) or not 3 <= len(vertices) <= 16:
        raise ValueError("footprint must have 3–16 vertices")
    polygon = [_point(v, "footprint_xy_m") for v in vertices]
    if len(set(polygon)) != len(polygon):
        raise ValueError("footprint has duplicate vertices")
    bends = [_cross(polygon[i], polygon[(i + 1) % len(polygon)],
                    polygon[(i + 2) % len(polygon)])
             for i in range(len(polygon))]
    if any(not isfinite(v) for v in bends) or (
            not (all(v >= 0 for v in bends) or all(v <= 0 for v in bends))):
        raise ValueError("footprint must be a simple convex polygon")
    double_area = sum(
        polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
        - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
        for i in range(len(polygon))
    )
    if not isfinite(double_area) or abs(double_area) <= 1e-12:
        raise ValueError("footprint has zero or invalid area")
    return polygon, height, state


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    ordered = sorted(set(points))
    if len(ordered) < 3:
        raise ValueError("support has insufficient unique vertices")
    lower: list[tuple[float, float]] = []
    for point in ordered:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(ordered):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    polygon = lower[:-1] + upper[:-1]
    if len(polygon) < 3:
        raise ValueError("support polygon is degenerate")
    return polygon


def inspect_static_support(spec: dict) -> dict:
    """Audit a static horizontal support *proxy*, never dynamic safety.

    Contact labels denote synthetic/assumed support, not physically measured
    ground reaction, friction, verified G1 contacts or load distribution.
    """
    if not isinstance(spec, dict) or set(spec) != {
            "schema_version", "terrain_class", "contacts",
            "com_projection_xy_m", "required_margin_m"}:
        raise ValueError("invalid support specification fields")
    if spec["schema_version"] != "1.0.0":
        raise ValueError("unsupported support specification version")
    terrain = spec["terrain_class"]
    if not isinstance(terrain, str) or terrain not in TERRAIN_CLASSES:
        raise ValueError("unknown terrain_class")
    contacts = spec["contacts"]
    if not isinstance(contacts, list) or not 1 <= len(contacts) <= 2:
        raise ValueError("expected one or two foot contact polygons")
    validated = [_validated_patch(value, idx) for idx, value in enumerate(contacts)]
    identifiers = [value["id"] for value in contacts]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("foot contact ids must be distinct")
    com = _point(spec["com_projection_xy_m"], "com_projection_xy_m")
    margin = _number(spec["required_margin_m"], "required_margin_m", nonnegative=True)

    status = "terrain_model_unsupported" if terrain != SUPPORTED_TERRAIN else None
    if status is None and any(state == "unknown" for _, _, state in validated):
        status = "contact_state_unknown"
    if status is None and len(validated) == 2 and abs(
            validated[0][1] - validated[1][1]) > 1e-9:
        status = "noncoplanar_contact_unsupported"

    report = {
        "schema_version": "1.0.0",
        "evidence_type": "synthetic_fixture",
        "model": "horizontal_static_support_projection_v1",
        "status": status,
        "contact_count": len(validated),
        "terrain_class": terrain,
        "required_margin_m": margin,
        "signed_support_margin_m": None,
        "support_polygon_xy_m": None,
        "dynamic_balance": "not_modelled",
        "friction_force_feasibility": "not_modelled",
        "kinematics_and_collision": "not_evaluated",
        "physical_robot_validation": "not_performed",
        "robot_adapter": "not_configured",
    }
    if status is not None:
        return report

    hull = _convex_hull([p for points, _, _ in validated for p in points])
    inside = all(_cross(hull[i], hull[(i + 1) % len(hull)], com) >= -1e-12
                 for i in range(len(hull)))
    distance = min(segment_distance(com, hull[i], hull[(i + 1) % len(hull)])
                   for i in range(len(hull)))
    if not isfinite(distance):
        raise ValueError("invalid support margin")
    signed = distance if inside else -distance
    report["signed_support_margin_m"] = signed
    report["support_polygon_xy_m"] = [list(xy) for xy in hull]
    if not inside:
        report["status"] = "outside_support_projection"
    elif distance <= 1e-12 or distance < margin:
        report["status"] = "insufficient_static_margin"
    else:
        report["status"] = "geometric_candidate_only"
    return report


def inspect_support_file(path: Path) -> dict:
    """Read a bounded local JSON fixture and append its source SHA-256."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("support input must be a local regular non-symlinked file")
    if source.stat().st_size > MAX_SPEC_BYTES:
        raise ValueError("support input exceeds byte limit")
    raw = source.read_bytes()
    if len(raw) > MAX_SPEC_BYTES:
        raise ValueError("support input exceeds byte limit")
    try:
        data = json.loads(raw.decode("utf-8"), parse_constant=lambda c: (
            _reject_constant(c)))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON support input") from exc
    result = inspect_static_support(data)
    result["source_sha256"] = sha256(raw).hexdigest()
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"unsupported non-finite JSON constant: {value}")
