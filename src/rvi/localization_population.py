"""P02 exploratory grouped planar-association study, not identity recognition.

Source geometry supplies anonymous synthetic bearing/range features through the
existing sensor adapter. Families (not frames) are the analysis units.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from itertools import product
import json
from math import atan2, hypot, pi
from pathlib import Path
import random

from .localization import IMAGE_METHODS, SENSOR_METHODS, run_sensor_localization
from .image_features import texture_templates
from .perception import load_sensor_config
from .scenarios import read_json
from .evidence import sha256_file, software_provenance

DESIGN = "planar_association_families_v1"
IMAGE_DESIGN = "planar_grayscale_association_v1"
SIMILARITIES = ("distinct", "similar")
PARTITIONS = ("development", "pilot", "holdout")
SEPARATIONS = ("near", "far")
OCCLUSIONS = ("clear", "blocked")
MAX_FAMILIES = 48


def _bytes(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha(blob: bytes) -> str:
    return sha256(blob).hexdigest()


def _seed(master: int, *parts: object) -> int:
    data = json.dumps([DESIGN, master, *parts], separators=(",", ":")).encode("utf-8")
    return int.from_bytes(sha256(data).digest()[:8], "big")


def _validate_spec(path: Path) -> tuple[dict, bytes, Path, bytes]:
    spec, raw = read_json(path)
    design = spec.get("design")
    expected = {"schema_version", "study_id", "design", "master_seed",
                "family_counts", "replicates_per_cell", "sensor"}
    if design == IMAGE_DESIGN:
        expected.add("appearance_levels")
        if spec.get("appearance_levels") != list(SIMILARITIES):
            raise ValueError("appearance levels must be distinct, similar")
    if set(spec) != expected:
        raise ValueError("invalid study02 population specification")
    if ((spec["schema_version"], spec["study_id"]) != ("1.0.0", "02")
            or design not in (DESIGN, IMAGE_DESIGN)):
        raise ValueError("unsupported study02 population design")
    seed, counts, repeats = (
        spec["master_seed"], spec["family_counts"], spec["replicates_per_cell"])
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("master_seed must be an unsigned 64-bit integer")
    if (not isinstance(counts, dict) or set(counts) != set(PARTITIONS)
            or any(type(counts[p]) is not int or not 1 <= counts[p] <= 16
                   for p in PARTITIONS) or sum(counts.values()) > MAX_FAMILIES):
        raise ValueError("invalid family counts")
    if type(repeats) is not int or not 1 <= repeats <= 4:
        raise ValueError("replicates_per_cell must be an integer in [1,4]")
    sensor = spec["sensor"]
    if (type(sensor) is not str or not sensor or Path(sensor).is_absolute()
            or ".." in Path(sensor).parts):
        raise ValueError("sensor needs a contained relative file path")
    source_root = path.resolve(strict=True).parent
    try:
        source = (source_root / sensor).resolve(strict=True)
    except OSError as exc:
        raise ValueError("sensor file is missing") from exc
    if not source.is_relative_to(source_root) or not source.is_file():
        raise ValueError("sensor file must be inside specification directory")
    load_sensor_config(source)
    return spec, raw, source, source.read_bytes()


def _layout(seed: int, family: str) -> tuple[float, float, float, int]:
    rng = random.Random(_seed(seed, family, "geometry"))
    return (rng.uniform(2.8, 3.4), rng.uniform(-0.15, 0.15),
            rng.uniform(-0.15, 0.15), rng.choice((-1, 1)))


def _study(family: str, sep: str, occ: str, replicate: int,
           layout: tuple[float, float, float, int], width: int,
           *, similarity: str | None = None,
           image_seed: int | None = None) -> tuple[dict, dict]:
    x, y, dx, direction = layout
    # The same family layout and target cue are reused in every crossed cell.
    other_y = y + direction * (0.18 if sep == "near" else 0.85)
    other_x = x + dx
    radius = 0.055
    image_suffix = f"_{similarity}" if similarity is not None else ""
    scene_id = f"{family}_{sep}_{occ}{image_suffix}_r{replicate:02d}"
    scene = {
        "schema_version": "1.0.0", "scene_id": scene_id,
        "evidence_type": "simulation",
        "start": {"x": 0.0, "y": 0.0, "yaw_rad": 0.0},
        "camera": {"horizontal_fov_rad": pi / 2, "min_range_m": 0.1,
                   "max_range_m": 10.0, "max_incidence_rad": pi / 3},
        "motion": {"linear_speed_m_s": 1.0, "angular_speed_rad_s": 1.0,
                   "robot_radius_m": 0.1, "capture_duration_s": 1.0,
                   "max_time_s": 10.0},
        "obstacles": ([] if occ == "clear" else
                      [{"x": x * 0.5, "y": y * 0.5, "radius_m": radius}]),
        "patches": [
            {"identifier": "target", "x": x, "y": y, "normal_rad": pi, "area_m2": 1.0},
            {"identifier": "distractor", "x": other_x, "y": other_y,
             "normal_rad": pi, "area_m2": 1.0},
        ],
        "route": [],
    }
    def cue(a: float, b: float) -> tuple[float, float]:
        return width * (0.5 - atan2(b, a) / (pi / 2)), hypot(a, b)

    u, distance = cue(x, y)
    u_absent, distance_absent = cue(other_x, other_y)
    study = {
        "schema_version": "1.0.0", "study_id": "02",
        "evidence_type": "simulation", "stage": "exploratory_not_confirmatory",
        "suite_id": scene_id, "scene": scene_id + ".scene.json",
        "sensor": "../sensor.json", "threshold": 0.25,
        "ambiguity_margin": 0.015,
        "requests": [
            {"request_id": "present", "capture_index": replicate,
             "expected_u_px": u, "expected_range_m": distance,
             "ground_truth_patch_id": "target"},
            {"request_id": "absent_hard_negative", "capture_index": replicate,
             "expected_u_px": u_absent, "expected_range_m": distance_absent,
             "ground_truth_patch_id": None},
        ],
    }
    if similarity is not None:
        if image_seed is None:
            raise ValueError("image seed is required for appearance studies")
        textures = texture_templates(image_seed, family, similarity)
        study["schema_version"] = "1.1.0"
        study["session_id"] = f"{family}_session_{replicate:02d}"
        study["appearance"] = {
            "textures": {"target": textures["target"],
                         "distractor": textures["distractor"]},
            "noise_seed": image_seed,
        }
        for request in study["requests"]:
            request["timestamp_s"] = float(replicate)
            request["template_pixels"] = (
                textures["target"] if request["ground_truth_patch_id"] == "target"
                else textures["absent"])
    return scene, study


def generate_localization_population(spec_path: Path, output_dir: Path) -> dict:
    """Generate disjoint synthetic families and content-hashed study inputs."""
    spec, raw, _, sensor_raw = _validate_spec(Path(spec_path))
    root = Path(output_dir)
    if root.exists():
        raise ValueError("output directory already exists")
    sensor_conf, _ = load_sensor_config(Path(spec_path).resolve().parent / spec["sensor"])
    image_mode = spec["design"] == IMAGE_DESIGN
    similarities = SIMILARITIES if image_mode else (None,)
    items: dict[str, bytes] = {"data/sensor.json": sensor_raw}
    records = []
    ordinal = 0
    for split in PARTITIONS:
        for _ in range(spec["family_counts"][split]):
            family = f"family_{ordinal:04d}"
            ordinal += 1
            layout = _layout(spec["master_seed"], family)
            for sep, occ, similarity, replicate in product(
                    SEPARATIONS, OCCLUSIONS, similarities,
                    range(spec["replicates_per_cell"])):
                scene, study = _study(family, sep, occ, replicate, layout,
                                      sensor_conf.width_px,
                                      similarity=similarity,
                                      image_seed=(spec["master_seed"]
                                                  if image_mode else None))
                base = f"data/{split}/{scene['scene_id']}"
                scene_name, study_name = base + ".scene.json", base + ".study.json"
                scene_raw, study_raw = _bytes(scene), _bytes(study)
                items[scene_name], items[study_name] = scene_raw, study_raw
                records.append({
                    "partition": split, "family": family, "separation": sep,
                    "occlusion": occ, "replicate": replicate,
                    "scene": scene_name, "scene_sha256": _sha(scene_raw),
                    "study": study_name, "study_sha256": _sha(study_raw),
                    **({"similarity": similarity,
                        "session_id": study["session_id"]}
                       if image_mode else {}),
                })
    manifest = {
        "schema_version": "1.0.0", "study_id": "02",
        "design": spec["design"],
        "evidence_type": "simulation", "stage": "exploratory_not_confirmatory",
        "sensor": "data/sensor.json", "sensor_sha256": _sha(sensor_raw),
        "spec_sha256": _sha(raw),
        "generator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "master_seed": spec["master_seed"],
        "family_counts": spec["family_counts"],
        "replicates_per_cell": spec["replicates_per_cell"],
        **({"appearance_levels": list(SIMILARITIES)} if image_mode else {}),
        "records": records,
    }
    items["manifest.json"] = _bytes(manifest)
    root.mkdir(parents=True, exist_ok=False)
    for relative, content in items.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(content)
    return manifest


def _verified(root: Path, relative: object, checksum: object) -> Path:
    if (type(relative) is not str or not relative or Path(relative).is_absolute()
            or type(checksum) is not str or len(checksum) != 64
            or any(c not in "0123456789abcdef" for c in checksum)):
        raise ValueError("invalid manifest file reference")
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("manifest file escapes study directory")
    if sha256_file(path) != checksum:
        raise ValueError("manifest input SHA-256 mismatch")
    return path


def analyze_localization_population(
    manifest_path: Path, partition: str = "pilot"
) -> dict:
    """Replay only development/pilot. Never read holdout study or scene files."""
    if partition not in ("development", "pilot"):
        raise ValueError("holdout analysis is prohibited in the exploratory runner")
    manifest_path = Path(manifest_path)
    manifest, raw = read_json(manifest_path)
    if (manifest.get("schema_version"), manifest.get("study_id"),
            manifest.get("stage")) != (
            "1.0.0", "02", "exploratory_not_confirmatory"):
        raise ValueError("invalid exploratory population manifest")
    design = manifest.get("design")
    if design not in (DESIGN, IMAGE_DESIGN):
        raise ValueError("unsupported population design")
    image_mode = design == IMAGE_DESIGN
    if image_mode and manifest.get("appearance_levels") != list(SIMILARITIES):
        raise ValueError("invalid appearance similarity levels")
    root = manifest_path.resolve(strict=True).parent
    sensor = _verified(root, manifest.get("sensor"), manifest.get("sensor_sha256"))
    load_sensor_config(sensor)
    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("population has no study records")
    families: dict[str, str] = {}
    signatures = set()
    selected = []
    for record in records:
        expected_fields = {"partition", "family", "separation", "occlusion",
                           "replicate", "scene", "scene_sha256",
                           "study", "study_sha256"}
        if image_mode:
            expected_fields |= {"similarity", "session_id"}
        if not isinstance(record, dict) or set(record) != expected_fields:
            raise ValueError("invalid population record")
        split, family = record["partition"], record["family"]
        if split not in PARTITIONS or type(family) is not str or not family:
            raise ValueError("invalid partition or family")
        if family in families and families[family] != split:
            raise ValueError("family crossed partition boundary")
        families[family] = split
        if (record["separation"] not in SEPARATIONS
                or record["occlusion"] not in OCCLUSIONS
                or type(record["replicate"]) is not int
                or not 0 <= record["replicate"] <= 3):
            raise ValueError("invalid condition or replicate")
        if image_mode:
            if (record["similarity"] not in SIMILARITIES
                    or record["session_id"] !=
                    f"{family}_session_{record['replicate']:02d}"):
                raise ValueError("invalid image factor or simulated session")
        key = (family, record["separation"], record["occlusion"],
               record.get("similarity"), record["replicate"])
        if key in signatures:
            raise ValueError("duplicate crossed-factor record")
        signatures.add(key)
        if split == partition:
            selected.append(record)
    if not selected:
        raise ValueError("requested exploratory partition is empty")
    reports = []
    for record in selected:
        _verified(root, record["scene"], record["scene_sha256"])
        study = _verified(root, record["study"], record["study_sha256"])
        data = run_sensor_localization(study)
        if data["sensor_sha256"] != manifest["sensor_sha256"]:
            raise ValueError("study sensor does not match manifest")
        if image_mode and (data["session_id"] != record["session_id"]
                           or set(data["selection_modes"]) != set(IMAGE_METHODS)):
            raise ValueError("image study is inconsistent with manifest")
        if not image_mode and set(data["selection_modes"]) != set(SENSOR_METHODS):
            raise ValueError("proxy study is inconsistent with manifest")
        reports.append((record, data))
    per_family: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list))
    strata = defaultdict(lambda: defaultdict(list))
    failures = defaultdict(int)
    methods = IMAGE_METHODS if image_mode else SENSOR_METHODS
    for record, report in reports:
        family = record["family"]
        for trial in report["trials"]:
            method = trial["method"]
            per_family[family][method].append(trial)
            stratum = (record["separation"], record["occlusion"],
                       *( (record["similarity"],) if image_mode else () ),
                       "present" if trial["target_present"] else "absent")
            strata[stratum][method].append(trial)
            if trial["measurement_status"] != "captured":
                failures[method] += 1

    def summarize(rows: list[dict]) -> dict:
        n = len(rows)
        wrong = sum(r["wrong_selection"] for r in rows)
        return {"eligible_requests": n, "wrong_selection": wrong,
                "wrong_selection_rate": wrong / n,
                "correct_selection": sum(r["status"] == "correct_selection" for r in rows),
                "correct_rejection": sum(r["status"] == "correct_rejection" for r in rows),
                "abstained": sum(r["decision"] != "selected" for r in rows)}

    family_results = {
        f: {m: summarize(per_family[f][m]) for m in methods}
        for f in sorted(per_family)
    }
    mean_risk = {
        m: sum(family_results[f][m]["wrong_selection_rate"] for f in family_results)
           / len(family_results)
        for m in methods
    }
    result = {
        "schema_version": "1.0.0", "study_id": "02",
        "evidence_type": "simulation", "status": "exploratory_not_confirmatory",
        "partition": partition, "independent_unit": "generated_family_model_draw",
        "family_count": len(family_results), "study_count": len(reports),
        "method_semantics": (
            "synthetic_grayscale_patch_mae_and_range_not_natural_images"
            if image_mode else "uncalibrated_bearing_range_proxies_not_image_recognition"),
        "manifest_sha256": _sha(raw),
        "source": software_provenance(),
        "family_results": family_results, "mean_family_wrong_risk": mean_risk,
        **({"paired_difference_grayscale_range_minus_grayscale":
            mean_risk["grayscale_range"] - mean_risk["grayscale_mae"]}
           if image_mode else {
               "paired_difference_joint_minus_bearing":
               mean_risk["joint_proxy"] - mean_risk["bearing_proxy"]}),
        "factor_strata": {
            ":".join(k): {m: summarize(rows) for m, rows in sorted(methods.items())}
            for k, methods in sorted(strata.items())
        },
        "missing_frames": dict(sorted(failures.items())),
        "inference": "descriptive_only_no_ci_no_p_value",
        "limitations": "synthetic_related_replicates_no_calibrated_images_or_physical_population",
    }
    return result
