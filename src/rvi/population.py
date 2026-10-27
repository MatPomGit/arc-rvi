"""Seeded exploratory scene-family draws; not a physical population model."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random

from .conditions import CONDITIONS, PARTITIONS, VERSION, _encoded, _hash
from .adapters.simulator import PlanarSimulator, load_scene

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


def _family_layout(master_seed: int, family: str) -> tuple[tuple[float, float, float], ...]:
    """One independent *pseudo-random model* draw per family, reused by replicates."""
    rng = random.Random(_seed(master_seed, family, "layout"))
    count = rng.randint(2, 4)
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


def generate_population(spec_path: Path, output_dir: Path) -> dict:
    """Generate paired, disjoint, synthetic families with hashes and no overwrites.

    The public holdout is *not blinded confirmation*. The output is exploratory.
    """
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

    # Fail closed on all content errors before making the output directory.
    # Exclusive file creation; rollback only paths created by this call.
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
            parent.mkdir(parents=True, exist_ok=True)
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
    return manifest
