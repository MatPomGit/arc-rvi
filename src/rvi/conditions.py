"""Seeded, family-separated planar scenes for exploratory study 01."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random

FAMILIES: dict[str, tuple[tuple[float, float], ...]] = {
    "parallel_pair": ((3.0, -0.7), (3.0, 0.7)),
    "staggered_pair": ((2.8, -0.8), (3.5, 0.6)),
    "stacked_triple": ((3.0, -1.0), (3.0, 0.0), (3.0, 1.0)),
    "offset_triple": ((2.6, -0.9), (3.4, 0.15), (2.9, 1.1)),
    "narrow_quad": ((3.0, -0.8), (3.1, -0.2), (2.9, 0.4), (3.0, 1.0)),
    "stepped_quad": ((2.6, -1.0), (3.0, -0.3), (3.5, 0.4), (2.8, 1.1)),
}
PARTITIONS = ("development", "pilot", "holdout")
CONDITIONS = ("nominal", "occluded")
VERSION = "1.0.0"


def _encoded(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _invalid_constant(value):
    raise ValueError(f"non-finite JSON value: {value}")


def _load_spec(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    spec = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=_invalid_constant)
    if not isinstance(spec, dict) or set(spec) != {
        "schema_version", "study_id", "master_seed", "replicates_per_family",
        "partitions", "conditions"
    }:
        raise ValueError("invalid study specification fields")
    if spec["schema_version"] != VERSION or spec["study_id"] != "01":
        raise ValueError("unsupported conditions schema or study")
    seed = spec["master_seed"]
    count = spec["replicates_per_family"]
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("master_seed must be an unsigned 64-bit integer")
    if type(count) is not int or not 1 <= count <= 16:
        raise ValueError("replicates_per_family must be from 1 to 16")
    if spec["conditions"] != list(CONDITIONS):
        raise ValueError("conditions must be nominal, occluded in that order")
    partitions = spec["partitions"]
    if not isinstance(partitions, dict) or set(partitions) != set(PARTITIONS):
        raise ValueError("expected development, pilot and holdout partitions")
    used = []
    for key in PARTITIONS:
        members = partitions[key]
        if not isinstance(members, list) or not members:
            raise ValueError("each partition needs at least one family")
        if any(type(item) is not str for item in members):
            raise ValueError("family names must be strings")
        used.extend(members)
    if len(used) != len(set(used)) or set(used) != set(FAMILIES):
        raise ValueError("families must be assigned exactly once across partitions")
    return spec, raw


def _replicate_seed(seed: int, family: str, replicate: int) -> int:
    data = f"rvi-conditions-v1:{seed}:{family}:{replicate}".encode("ascii")
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "big")


def _scene(family: str, replicate: int, replicate_seed: int, condition: str) -> dict:
    rng = random.Random(replicate_seed)
    patches = []
    route = []
    for index, (x, y) in enumerate(FAMILIES[family], 1):
        px, py = x + rng.uniform(-0.12, 0.12), y + rng.uniform(-0.12, 0.12)
        vy = py + rng.uniform(-0.08, 0.08)
        patches.append({"identifier": f"surface_{index:02d}", "x": px, "y": py,
                        "normal_rad": math.pi, "area_m2": 1.0})
        route.append({"x": 0.0, "y": vy, "yaw_rad": 0.0})
    target, candidate = patches[0], route[0]
    obstacle = {"x": target["x"] / 2, "y": (target["y"] + candidate["y"]) / 2,
                "radius_m": 0.28}
    return {
        "schema_version": VERSION,
        "scene_id": f"{family}_r{replicate:03d}_{condition}",
        "evidence_type": "simulation",
        "start": {"x": 0.0, "y": 0.0, "yaw_rad": 0.0},
        "camera": {"horizontal_fov_rad": math.pi / 2, "min_range_m": 0.1,
                   "max_range_m": 5.0, "max_incidence_rad": math.pi / 3},
        "motion": {"linear_speed_m_s": 1.0, "angular_speed_rad_s": 1.0,
                   "robot_radius_m": 0.1, "capture_duration_s": 1.0,
                   "max_time_s": 16.0},
        "obstacles": [] if condition == "nominal" else [obstacle],
        "patches": patches,
        "route": route,
    }


def generate_conditions(spec_path: Path, output_dir: Path) -> dict:
    """Create paired scene files, disjoint partition suites, and hash manifest.

    The output must not exist; this never overwrites prior research artifacts.
    """
    spec, raw = _load_spec(spec_path)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError("output directory already exists")
    manifest = {
        "schema_version": VERSION, "study_id": "01",
        "evidence_type": "simulation", "stage": "exploratory_not_confirmatory",
        "visibility_access": "known_geometry_oracle",
        "source_generator_sha256": _hash(Path(__file__).read_bytes()),
        "spec_sha256": _hash(raw),
        "master_seed": spec["master_seed"],
        "replicates_per_family": spec["replicates_per_family"],
        "partitions": spec["partitions"],
        "conditions": list(CONDITIONS),
        "scenes": [], "suites": {},
    }
    files: dict[str, bytes] = {}
    for split in PARTITIONS:
        entries = []
        for family in spec["partitions"][split]:
            for replicate in range(spec["replicates_per_family"]):
                seed = _replicate_seed(spec["master_seed"], family, replicate)
                pair_id = f"{family}_r{replicate:03d}"
                for condition in CONDITIONS:
                    name = f"{pair_id}_{condition}.json"
                    relative = f"scenes/{split}/{name}"
                    scene = _scene(family, replicate, seed, condition)
                    content = _encoded(scene)
                    files[relative] = content
                    entries.append(f"../{relative}")
                    manifest["scenes"].append({
                        "path": relative, "scene_id": scene["scene_id"],
                        "partition": split, "family": family, "replicate": replicate,
                        "paired_seed": seed, "pair_id": pair_id,
                        "condition": condition, "sha256": _hash(content),
                    })
        suite_relative = f"suites/{split}.json"
        suite_content = _encoded({
            "schema_version": VERSION, "suite_id": f"study01_{split}",
            "evidence_type": "simulation", "scenes": entries,
        })
        files[suite_relative] = suite_content
        manifest["suites"][split] = {
            "path": suite_relative, "sha256": _hash(suite_content),
        }
    files["manifest.json"] = _encoded(manifest)
    # Validate/encode all files before creating the directory.
    output_dir.mkdir(parents=True, exist_ok=False)
    for relative, content in files.items():
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(content)
    return manifest
