"""Uncalibrated planar sensor features with evaluator-only geometric truth.

No image rendering, target recognition or physical sensing is implemented.
Pass only the first return value to an experimental policy.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import json
from math import atan2, hypot, isfinite, pi, remainder
from pathlib import Path
import random

from .adapters.simulator import PlanarScene, PlanarSimulator, validate_pose
from .interfaces import CameraPose
from .scenarios import read_json

MODEL = "planar_feature_sensor_v1"


@dataclass(frozen=True)
class SensorConfig:
    width_px: int
    illumination_relative: float
    exposure_relative: float
    focus_fraction: float
    motion_blur_fraction: float
    pixel_noise_sd: float
    range_noise_sd_m: float
    brightness_noise_sd: float
    detection_dropout: float
    frame_dropout: float
    master_seed: int

    def __post_init__(self) -> None:
        if type(self.width_px) is not int or not 32 <= self.width_px <= 8192:
            raise ValueError("width_px must be an integer in [32, 8192]")
        if type(self.master_seed) is not int or not 0 <= self.master_seed < 2**64:
            raise ValueError("master_seed must be an unsigned 64-bit integer")
        limits = {
            "illumination_relative": (0, 4),
            "exposure_relative": (0, 4),
            "focus_fraction": (0, 1),
            "motion_blur_fraction": (0, 1),
            "pixel_noise_sd": (0, 32),
            "range_noise_sd_m": (0, 2),
            "brightness_noise_sd": (0, 64),
            "detection_dropout": (0, 1),
            "frame_dropout": (0, 1),
        }
        for key, (low, high) in limits.items():
            value = getattr(self, key)
            if type(value) not in (int, float) or not isfinite(value) or not low <= value <= high:
                raise ValueError(f"{key} must be finite in [{low}, {high}]")


def load_sensor_config(path: Path) -> tuple[SensorConfig, bytes]:
    """Read and strictly validate a simulation-only, versioned factor preset."""
    data, raw = read_json(Path(path))
    expected = {"schema_version", "evidence_type", "calibration_state"} | {
        field.name for field in fields(SensorConfig)
    }
    if set(data) != expected or (
        data["schema_version"], data["evidence_type"], data["calibration_state"]
    ) != ("1.0.0", "simulation", "uncalibrated_synthetic"):
        raise ValueError("unsupported or incomplete synthetic sensor specification")
    return SensorConfig(**{field.name: data[field.name] for field in fields(SensorConfig)}), raw


def _stream(seed: int, scene_id: str, index: int, key: str) -> random.Random:
    """Derive a stable stream without Python's process-randomized hash()."""
    source = json.dumps([seed, scene_id, index, key], ensure_ascii=False).encode("utf-8")
    return random.Random(int.from_bytes(sha256(source).digest()[:8], "big"))


def simulate_sensor(
    scene: PlanarScene,
    pose: CameraPose,
    config: SensorConfig,
    *,
    capture_index: int = 0,
    timestamp_s: float = 0.0,
) -> tuple[dict, dict]:
    """Return (policy_observation, evaluator_truth) as separate records.

    Ground-truth patch identifiers are never included in the policy record.
    This is a 1D angular feature model, not image rendering or actual perception.
    """
    if not isinstance(config, SensorConfig):
        raise ValueError("config must be SensorConfig")
    if type(capture_index) is not int or not 0 <= capture_index < 2**32:
        raise ValueError("capture_index must be an unsigned 32-bit integer")
    if type(timestamp_s) not in (int, float) or not isfinite(timestamp_s) or timestamp_s < 0:
        raise ValueError("timestamp_s must be nonnegative and finite")
    validate_pose(pose)
    visible = set(PlanarSimulator(scene).visible_patches(pose))
    frame_rng = _stream(config.master_seed, scene.identifier, capture_index, "frame")
    missing = frame_rng.random() < config.frame_dropout
    detections = []
    references = []
    for patch in sorted(scene.patches, key=lambda item: item.identifier):
        is_visible = patch.identifier in visible
        detected = False
        if is_visible and not missing:
            rng = _stream(config.master_seed, scene.identifier, capture_index,
                          f"patch:{patch.identifier}")
            if rng.random() >= config.detection_dropout:
                dx, dy = patch.x - pose.x, patch.y - pose.y
                angle = remainder(atan2(dy, dx) - pose.yaw_rad, 2 * pi)
                # +y is left in world coordinates; increasing pixel u is right.
                pixel_u = config.width_px * (0.5 - angle / scene.camera.horizontal_fov_rad)
                brightness = 128 * config.illumination_relative * config.exposure_relative
                detection = {
                    "u_px": min(config.width_px, max(
                        0.0, pixel_u + rng.gauss(0, config.pixel_noise_sd))),
                    "range_m": max(0.0, hypot(dx, dy) + rng.gauss(0, config.range_noise_sd_m)),
                    "brightness_gray_8bit": round(min(255, max(
                        0, brightness + rng.gauss(0, config.brightness_noise_sd)))),
                    "sharpness_proxy": config.focus_fraction * (1 - config.motion_blur_fraction),
                }
                detections.append((patch.identifier, detection))
                detected = True
        references.append({
            "patch_id": patch.identifier, "geometry_visible": is_visible,
            "detected": detected, "detection_id": None,
        })
    detections.sort(key=lambda item: item[1]["u_px"])
    policy_detections = []
    links = {}
    for index, (patch_id, features) in enumerate(detections, 1):
        identifier = f"feature_{index:04d}"
        links[patch_id] = identifier
        policy_detections.append({"id": identifier, **features})
    for entry in references:
        entry["detection_id"] = links.get(entry["patch_id"])
    policy = {
        "schema_version": "1.0.0", "evidence_type": "simulation", "model": MODEL,
        "measurement_frame": "camera_horizontal_1d_px", "timestamp_s": float(timestamp_s),
        "capture_index": capture_index, "width_px": config.width_px,
        "status": "measurement_missing" if missing else "captured",
        "detections": policy_detections,
    }
    evaluator = {
        "schema_version": "1.0.0", "evidence_type": "simulation",
        "oracle": "known_planar_geometry", "scene_id": scene.identifier,
        "capture_index": capture_index, "geometry_references": references,
    }
    return policy, evaluator
