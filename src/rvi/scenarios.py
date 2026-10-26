"""Strict JSON input for small public inspection fixtures."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path

from .models import Viewpoint


def read_json(path: Path) -> tuple[dict, bytes]:
    """Read once so provenance hashes identify the bytes actually parsed."""
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"non-finite JSON value: {value}")

    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                         parse_constant=reject_constant)
    if not isinstance(payload, dict):
        raise ValueError("JSON document must be an object")
    return payload, raw


def number(value, name: str, *, nonnegative: bool = False) -> float:
    try:
        valid = type(value) in (float, int) and isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite number")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return float(value)


def name(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{field} must contain valid Unicode") from exc
    return value


@dataclass(frozen=True)
class Scenario:
    identifier: str
    required_regions: tuple[str, ...]
    viewpoints: tuple[Viewpoint, ...]
    start_xy: tuple[float, float]


def load_scenario(path: Path) -> tuple[Scenario, bytes]:
    payload, raw = read_json(path)
    fields = {"scenario_id", "evidence_type", "required_regions", "viewpoints", "start_xy"}
    if payload.keys() - fields:
        raise ValueError("unknown scenario fields")
    if not {"scenario_id", "evidence_type", "required_regions", "viewpoints"} <= payload.keys():
        raise ValueError("scenario is missing required fields")
    if payload["evidence_type"] not in ("fixture", "synthetic_fixture"):
        raise ValueError("only fixture scenarios are supported")
    identifier = name(payload["scenario_id"], "scenario_id")
    regions = payload["required_regions"]
    if not isinstance(regions, list) or not regions:
        raise ValueError("required_regions must be a nonempty list")
    required = tuple(name(region, "region") for region in regions)
    if len(set(required)) != len(required):
        raise ValueError("required_regions must be unique")
    start = payload.get("start_xy", [0.0, 0.0])
    if not isinstance(start, list) or len(start) != 2:
        raise ValueError("start_xy must contain two coordinates")
    start_xy = tuple(number(value, "start coordinate") for value in start)
    entries = payload["viewpoints"]
    if not isinstance(entries, list):
        raise ValueError("viewpoints must be a list")
    views = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.keys() != {"id", "x", "y", "regions"}:
            raise ValueError("each viewpoint needs id, x, y and regions")
        if not isinstance(entry["regions"], list):
            raise ValueError("viewpoint regions must be a list")
        view = Viewpoint(name(entry["id"], "viewpoint id"), number(entry["x"], "x"),
                         number(entry["y"], "y"),
                         tuple(name(region, "region") for region in entry["regions"]))
        if set(view.visible_regions) - set(required):
            raise ValueError("viewpoint contains an undeclared region")
        views.append(view)
    if len({view.identifier for view in views}) != len(views):
        raise ValueError("duplicate viewpoint identifiers")
    return Scenario(identifier, required, tuple(views), start_xy), raw
