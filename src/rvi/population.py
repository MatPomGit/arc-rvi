"""Seeded exploratory scene-family draws; not a physical population model."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from itertools import product
import json
import math
from pathlib import Path
import random

from .conditions import CONDITIONS, PARTITIONS, VERSION, _encoded, _hash
from .perception import SensorConfig
from .scenarios import read_json

DESIGN = "sampled_geometry_v1"
DISTRIBUTION = {
    "patch_count": [2, 4],
    "patch_x_m": [2.6, 3.6],
    "patch_y_span_m": [-0.9, 0.9],
    "family_y_jitter_m": [-0.05, 0.05],
    "replicate_xy_jitter_m": [-0.04, 0.04],
    "patch_area_m2": [0.75, 1.25],
    "occluder_radius_m": 0.28,
}
MAX_FAMILIES = 128
MAX_SCENES = 2048
FACTORIAL_DESIGN = "sampled_factorial_v1"
FACTOR_LEVELS = {
    "occlusion": ("none", "moderate", "strong"),
    "illumination": ("low", "reference"),
    "clutter": ("none", "dense"),
}
OCCLUDER_RADIUS_M = {"none": 0.0, "moderate": 0.12, "strong": 0.32}
ILLUMINATION_RELATIVE = {"low": 0.35, "reference": 1.0}



def _pairs(entries):
    result = {}
    for key, value in entries:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def _read_spec(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    spec = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=_reject_constant)
    expected = {"schema_version", "study_id", "design", "master_seed",
                "replicates_per_family", "conditions", "family_counts"}
    if not isinstance(spec, dict) or set(spec) != expected:
        raise ValueError("population specification has invalid fields")
    if (spec["schema_version"], spec["study_id"], spec["design"]) != (VERSION, "01", DESIGN):
        raise ValueError("unsupported population design or schema version")
    seed, repeats, counts = (spec[key] for key in
                             ("master_seed", "replicates_per_family", "family_counts"))
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("master_seed must be an unsigned 64-bit integer")
    if type(repeats) is not int or not 1 <= repeats <= 8:
        raise ValueError("replicates_per_family must be from 1 to 8")
    if spec["conditions"] != list(CONDITIONS):
        raise ValueError("conditions must be nominal, occluded in that order")
    if not isinstance(counts, dict) or set(counts) != set(PARTITIONS):
        raise ValueError("family_counts must include development, pilot and holdout")
    if any(type(counts[split]) is not int or not 1 <= counts[split] <= 64
           for split in PARTITIONS):
        raise ValueError("family_counts values must be integers from 1 to 64")
    families = sum(counts.values())
    if families > MAX_FAMILIES or families * repeats * len(CONDITIONS) > MAX_SCENES:
        raise ValueError("population design exceeds the configured generation limit")
    return spec, raw


def _seed(master_seed: int, *parts: object) -> int:
    value = ":".join(("rvi-population-v1", str(master_seed),
                      *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(value.encode("ascii")).digest()[:8], "big")


def _family_layout(master_seed: int, family: str,
                   patch_count: int | None = None) -> tuple[tuple[float, float, float], ...]:
    """One independent *pseudo-random model* draw per family, reused by replicates."""
    rng = random.Random(_seed(master_seed, family, "layout"))
    count = rng.randint(2, 4) if patch_count is None else patch_count
    layout = []
    for index in range(count):
        center_y = -0.9 + 1.8 * index / (count - 1)
        layout.append((rng.uniform(2.6, 3.6),
                       center_y + rng.uniform(-0.05, 0.05),
                       rng.uniform(0.75, 1.25)))
    return tuple(layout)


def _scene(family: str, repeat: int, replicate_seed: int, condition: str,
           layout: tuple[tuple[float, float, float], ...]) -> dict:
    rng = random.Random(replicate_seed)
    patches, poses = [], []
    for index, (x, y, area) in enumerate(layout, start=1):
        px = x + rng.uniform(-0.04, 0.04)
        py = y + rng.uniform(-0.04, 0.04)
        vy = py + rng.uniform(-0.025, 0.025)
        patches.append({"identifier": f"surface_{index:02d}", "x": px, "y": py,
                        "normal_rad": math.pi, "area_m2": area})
        poses.append({"x": 0.0, "y": vy, "yaw_rad": 0.0})
    target, pose = patches[0], poses[0]
    blocker = {"x": target["x"] / 2,
               "y": (target["y"] + pose["y"]) / 2,
               "radius_m": DISTRIBUTION["occluder_radius_m"]}
    return {
        "schema_version": VERSION,
        "scene_id": f"{family}_r{repeat:03d}_{condition}",
        "evidence_type": "simulation",
        "start": {"x": 0.0, "y": 0.0, "yaw_rad": 0.0},
        "camera": {"horizontal_fov_rad": math.pi / 2, "min_range_m": 0.1,
                   "max_range_m": 5.0, "max_incidence_rad": math.pi / 3},
        "motion": {"linear_speed_m_s": 1.0, "angular_speed_rad_s": 1.0,
                   "robot_radius_m": 0.1, "capture_duration_s": 1.0,
                   "max_time_s": 16.0},
        "obstacles": [] if condition == "nominal" else [blocker],
        "patches": patches, "route": poses,
    }


def _write_artifacts(output_dir: Path, payloads: dict[str, bytes]) -> None:
    """Exclusively write new results and roll back only this call's artifacts."""
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("output directory already exists")
    written: list[Path] = []
    directories: set[Path] = set()
    created = False
    try:
        output_dir.mkdir(parents=True, exist_ok=False)
        created = True
        for relative, raw_file in payloads.items():
            destination = output_dir / relative
            parent = destination.parent
            while parent != output_dir:
                directories.add(parent)
                parent = parent.parent
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as file:
                written.append(destination)
                file.write(raw_file)
    except BaseException:
        if created:
            for path in reversed(written):
                path.unlink(missing_ok=True)
            for path in sorted(directories, key=lambda p: len(p.parts), reverse=True):
                try:
                    path.rmdir()
                except OSError:
                    pass
            try:
                output_dir.rmdir()
            except OSError:
                pass
        raise

def _factorial_spec(path: Path) -> tuple[dict, bytes]:
    spec, raw = read_json(path)
    required = {"schema_version", "study_id", "design", "master_seed",
                "replicates_per_family", "family_counts", "factors"}
    if not isinstance(spec, dict) or set(spec) != required:
        raise ValueError("invalid factorial specification fields")
    if (spec["schema_version"], spec["study_id"], spec["design"]) != (
            VERSION, "01", FACTORIAL_DESIGN):
        raise ValueError("unsupported factorial design")
    if spec["factors"] != {key: list(levels)
                          for key, levels in FACTOR_LEVELS.items()}:
        raise ValueError("unsupported factorial levels or order")
    seed, repeats, counts = (spec[key] for key in
                             ("master_seed", "replicates_per_family", "family_counts"))
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("invalid factorial master_seed")
    if type(repeats) is not int or not 1 <= repeats <= 4:
        raise ValueError("factorial replicates must be in [1, 4]")
    if not isinstance(counts, dict) or set(counts) != set(PARTITIONS):
        raise ValueError("invalid factorial partitions")
    if any(type(counts[split]) is not int or not 3 <= counts[split] <= 48
           or counts[split] % 3 for split in PARTITIONS):
        raise ValueError("family counts must be multiples of 3 in [3, 48]")
    total = sum(counts.values())
    cells = math.prod(len(levels) for levels in FACTOR_LEVELS.values())
    if total > MAX_FAMILIES or total * repeats * cells > MAX_SCENES:
        raise ValueError("factorial generation exceeds configured scene limit")
    return spec, raw


def _factorial_obstacles(scene: dict, occlusion: str, clutter: str) -> list[dict]:
    """Occlude patch one and optionally add two nuisance discs near patch two."""
    obstacles = []
    target, candidate = scene["patches"][0], scene["route"][0]
    radius = OCCLUDER_RADIUS_M[occlusion]
    if radius:
        obstacles.append({"x": target["x"] / 2,
                          "y": (target["y"] + candidate["y"]) / 2,
                          "radius_m": radius})
    if clutter == "dense":
        patch, view = scene["patches"][1], scene["route"][1]
        for ratio in (0.4, 0.65):
            obstacles.append({"x": patch["x"] * ratio,
                              "y": view["y"] + ratio * (patch["y"] - view["y"]),
                              "radius_m": 0.12})
    return obstacles


def _factor_sensor(seed: int, illumination: str) -> dict:
    config = SensorConfig(640, ILLUMINATION_RELATIVE[illumination], 1, 1, 0,
                          0.5, 0.01, 2, 0.05, 0, seed)
    return {"schema_version": VERSION, "evidence_type": "simulation",
            "calibration_state": "uncalibrated_synthetic", **asdict(config)}


def _factorial_population(spec_path: Path, output_dir: Path) -> dict:
    """Generate separate crossed pilot/development/holdout *synthetic* suites."""
    spec, raw = _factorial_spec(spec_path)
    members: dict[str, list[str]] = {}
    index = 0
    for split in PARTITIONS:
        members[split] = []
        for _ in range(spec["family_counts"][split]):
            index += 1
            members[split].append(f"factor_{index:04d}")
    cells = []
    for occlusion, illumination, clutter in product(*FACTOR_LEVELS.values()):
        cell_id = f"o_{occlusion}__i_{illumination}__c_{clutter}"
        cells.append((cell_id, {
            "occlusion": occlusion, "illumination": illumination,
            "clutter": clutter,
        }))
    manifest = {
        "schema_version": VERSION, "study_id": "01",
        "design": FACTORIAL_DESIGN, "evidence_type": "simulation",
        "stage": "exploratory_not_confirmatory",
        "visibility_access": "evaluator_only_when_sensor_mode_enabled",
        "master_seed": spec["master_seed"],
        "replicates_per_family": spec["replicates_per_family"],
        "partitions": members, "factor_levels": spec["factors"],
        "geometry_strata_patch_counts": [2, 3, 4],
        "cells": [{"cell_id": cell, **factors} for cell, factors in cells],
        "source_generator_sha256": _hash(Path(__file__).read_bytes()),
        "spec_sha256": _hash(raw), "scenes": [], "suites": {},
        "sensor_configs": {}, "holdout_state": "generated_not_blinded_or_frozen",
    }
    payloads: dict[str, bytes] = {}
    for illumination in FACTOR_LEVELS["illumination"]:
        relative = f"sensors/{illumination}.json"
        encoded = _encoded(_factor_sensor(spec["master_seed"], illumination))
        payloads[relative] = encoded
        manifest["sensor_configs"][illumination] = {
            "path": relative, "sha256": _hash(encoded),
            "illumination_relative": ILLUMINATION_RELATIVE[illumination],
        }
    for split in PARTITIONS:
        grouped = {cell: [] for cell, _ in cells}
        for family_index, family in enumerate(members[split]):
            patch_count = 2 + family_index % 3
            layout = _family_layout(spec["master_seed"], family, patch_count)
            for replicate in range(spec["replicates_per_family"]):
                seed = _seed(spec["master_seed"], family, replicate, "replicate")
                pair_id = f"{family}_r{replicate:03d}"
                base = _scene(family, replicate, seed, "nominal", layout)
                for cell, factors in cells:
                    scene = dict(base)
                    scene["scene_id"] = f"{pair_id}__{cell}"
                    scene["obstacles"] = _factorial_obstacles(
                        scene, factors["occlusion"], factors["clutter"])
                    relative = f"scenes/{split}/{scene['scene_id']}.json"
                    encoded = _encoded(scene)
                    payloads[relative] = encoded
                    grouped[cell].append("../../" + relative)
                    manifest["scenes"].append({
                        "path": relative, "scene_id": scene["scene_id"],
                        "partition": split, "family": family,
                        "pair_id": pair_id, "replicate": replicate,
                        "paired_seed": seed, "geometry_patch_count": patch_count,
                        "cell_id": cell, "factors": dict(factors),
                        "sha256": _hash(encoded),
                    })
        manifest["suites"][split] = {}
        for cell, factors in cells:
            relative = f"suites/{split}/{cell}.json"
            encoded = _encoded({
                "schema_version": VERSION,
                "suite_id": f"study01_{split}_{cell}",
                "evidence_type": "simulation", "scenes": grouped[cell],
            })
            payloads[relative] = encoded
            manifest["suites"][split][cell] = {
                "path": relative, "sha256": _hash(encoded),
                "sensor_config": manifest["sensor_configs"][
                    factors["illumination"]]["path"],
            }
    payloads["manifest.json"] = _encoded(manifest)
    _write_artifacts(output_dir, payloads)
    return manifest


def generate_population(spec_path: Path, output_dir: Path) -> dict:
    """Generate paired, disjoint, synthetic families with hashes and no overwrites.

    The public holdout is *not blinded confirmation*. The output is exploratory.
    """
    design, _ = read_json(Path(spec_path))
    if isinstance(design, dict) and design.get("design") == FACTORIAL_DESIGN:
        return _factorial_population(Path(spec_path), output_dir)
    spec, raw = _read_spec(Path(spec_path))
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("output directory already exists")
    partition_members = {}
    index = 0
    for split in PARTITIONS:
        members = []
        for _ in range(spec["family_counts"][split]):
            index += 1
            members.append(f"geom_{index:04d}")
        partition_members[split] = members
    manifest = {
        "schema_version": VERSION, "study_id": "01",
        "design": DESIGN, "evidence_type": "simulation",
        "stage": "exploratory_not_confirmatory",
        "visibility_access": "known_geometry_oracle",
        "master_seed": spec["master_seed"],
        "replicates_per_family": spec["replicates_per_family"],
        "partitions": partition_members,
        "conditions": list(CONDITIONS),
        "distribution": DISTRIBUTION,
        "source_generator_sha256": _hash(Path(__file__).read_bytes()),
        "spec_sha256": _hash(raw),
        "scenes": [], "suites": {},
    }
    payloads: dict[str, bytes] = {}
    for split in PARTITIONS:
        entries = []
        for family in partition_members[split]:
            layout = _family_layout(spec["master_seed"], family)
            for repeat in range(spec["replicates_per_family"]):
                paired_seed = _seed(spec["master_seed"], family, repeat, "replicate")
                pair_id = f"{family}_r{repeat:03d}"
                for condition in CONDITIONS:
                    relative = f"scenes/{split}/{pair_id}_{condition}.json"
                    scene = _scene(family, repeat, paired_seed, condition, layout)
                    encoded = _encoded(scene)
                    payloads[relative] = encoded
                    entries.append("../" + relative)
                    manifest["scenes"].append({
                        "path": relative, "scene_id": scene["scene_id"],
                        "partition": split, "family": family,
                        "replicate": repeat, "paired_seed": paired_seed,
                        "pair_id": pair_id, "condition": condition,
                        "sha256": _hash(encoded),
                    })
        relative = f"suites/{split}.json"
        encoded = _encoded({"schema_version": VERSION,
                            "suite_id": f"study01_{split}",
                            "evidence_type": "simulation",
                            "scenes": entries})
        payloads[relative] = encoded
        manifest["suites"][split] = {"path": relative, "sha256": _hash(encoded)}
    payloads["manifest.json"] = _encoded(manifest)

    _write_artifacts(output_dir, payloads)
    return manifest
