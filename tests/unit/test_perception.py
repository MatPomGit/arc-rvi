"""Independent analytic feature-projection checks and sensor/evaluator isolation."""

from __future__ import annotations

from dataclasses import replace
import json
from math import pi, sqrt
from pathlib import Path
import tempfile
import unittest

from rvi.adapters.simulator import (CameraModel, MotionModel, PlanarScene,
                                    SurfacePatch, load_scene)
from rvi.interfaces import CameraPose
from rvi.perception import SensorConfig, load_sensor_config, simulate_sensor

ROOT = Path(__file__).resolve().parents[2]
PRESET = ROOT / "simulation/conditions/sensor_exploratory.json"


def example_scene() -> PlanarScene:
    return PlanarScene(
        "test_geometry", CameraPose(0, 0, 0),
        CameraModel(pi / 2, .1, 10, pi / 2),
        MotionModel(1, 1, 0, 1, 20), (),
        (SurfacePatch("left_hidden_identity", 2, 2, pi, 1),
         SurfacePatch("center_hidden_identity", 2, 0, pi, 1),
         SurfacePatch("right_hidden_identity", 2, -2, pi, 1)), (),
    )


def config(**changes) -> SensorConfig:
    base = SensorConfig(640, 1, 1, 1, 0, 0, 0, 0, 0, 0, 37)
    return replace(base, **changes)


class SyntheticSensorTests(unittest.TestCase):
    def test_analytic_left_center_right_projection_and_truth_isolation(self):
        policy, reference = simulate_sensor(example_scene(), CameraPose(0, 0, 0),
                                            config(), timestamp_s=1.25)
        self.assertEqual(policy["status"], "captured")
        self.assertEqual(policy["timestamp_s"], 1.25)
        self.assertEqual(policy["measurement_frame"], "camera_horizontal_1d_px")
        self.assertEqual(len(policy["detections"]), 3)
        self.assertEqual([d["u_px"] for d in policy["detections"]],
                         [0, 320, 640])
        self.assertEqual([d["range_m"] for d in policy["detections"]],
                         [sqrt(8), 2, sqrt(8)])
        self.assertEqual([d["brightness_gray_8bit"] for d in policy["detections"]],
                         [128, 128, 128])
        self.assertEqual([d["sharpness_proxy"] for d in policy["detections"]], [1, 1, 1])
        visible = {r["patch_id"] for r in reference["geometry_references"]
                   if r["geometry_visible"]}
        self.assertEqual(visible, {"left_hidden_identity", "center_hidden_identity",
                                   "right_hidden_identity"})
        serialized = json.dumps(policy)
        self.assertNotIn("hidden_identity", serialized)
        self.assertNotIn("patch_id", serialized)
        self.assertNotIn("oracle", serialized)
        self.assertNotIn("x", policy["detections"][0])
        self.assertEqual(
            {r["detection_id"] for r in reference["geometry_references"]},
            {d["id"] for d in policy["detections"]},
        )

    def test_noise_replay_and_paired_environmental_factors(self):
        scene = example_scene()
        original = config(pixel_noise_sd=3, range_noise_sd_m=.2, brightness_noise_sd=4)
        nominal, ground_truth = simulate_sensor(scene, scene.start, original,
                                                capture_index=9)
        self.assertEqual((nominal, ground_truth),
                         simulate_sensor(scene, scene.start, original, capture_index=9))
        dim, _ = simulate_sensor(scene, scene.start,
                                 replace(original, illumination_relative=.5),
                                 capture_index=9)
        self.assertEqual([d["u_px"] for d in nominal["detections"]],
                         [d["u_px"] for d in dim["detections"]])
        self.assertEqual([d["range_m"] for d in nominal["detections"]],
                         [d["range_m"] for d in dim["detections"]])
        self.assertNotEqual([d["brightness_gray_8bit"] for d in nominal["detections"]],
                            [d["brightness_gray_8bit"] for d in dim["detections"]])
        changed, _ = simulate_sensor(scene, scene.start, original, capture_index=10)
        self.assertNotEqual(nominal["detections"], changed["detections"])

    def test_geometry_occlusion_and_no_false_detections(self):
        scene, _ = load_scene(ROOT / "simulation/worlds/planar_inspection.json")
        policy, evaluator = simulate_sensor(scene, scene.start, config())
        self.assertEqual({r["patch_id"] for r in evaluator["geometry_references"]
                          if r["geometry_visible"]}, {"lower"})
        self.assertEqual(len(policy["detections"]), 1)
        self.assertEqual(sum(r["detected"] for r in evaluator["geometry_references"]), 1)
        hidden = next(r for r in evaluator["geometry_references"] if r["patch_id"] == "upper")
        self.assertFalse(hidden["geometry_visible"])
        self.assertFalse(hidden["detected"])

    def test_dropouts_and_quality_proxies(self):
        scene = example_scene()
        missing, truth = simulate_sensor(scene, scene.start, config(frame_dropout=1))
        self.assertEqual(missing["status"], "measurement_missing")
        self.assertFalse(missing["detections"])
        self.assertTrue(all(r["geometry_visible"] for r in truth["geometry_references"]))
        self.assertTrue(all(not r["detected"] for r in truth["geometry_references"]))
        no_features, reference = simulate_sensor(scene, scene.start,
                                                 config(detection_dropout=1))
        self.assertEqual(no_features["status"], "captured")
        self.assertFalse(no_features["detections"])
        self.assertTrue(all(not r["detected"] for r in reference["geometry_references"]))
        blurry, _ = simulate_sensor(scene, scene.start,
                                    config(focus_fraction=.7, motion_blur_fraction=.5))
        self.assertEqual([d["sharpness_proxy"] for d in blurry["detections"]],
                         [.35] * 3)
        dark, _ = simulate_sensor(scene, scene.start, config(illumination_relative=0))
        self.assertTrue(all(d["brightness_gray_8bit"] == 0 for d in dark["detections"]))

    def test_invalid_config_and_rejected_simulation_inputs(self):
        invalids = [
            {"width_px": True}, {"width_px": 20}, {"width_px": 9999},
            {"master_seed": -1}, {"master_seed": True}, {"master_seed": 2**64},
            {"illumination_relative": float("nan")},
            {"exposure_relative": float("inf")},
            {"pixel_noise_sd": -1}, {"range_noise_sd_m": 3},
            {"brightness_noise_sd": 65}, {"motion_blur_fraction": 1.1},
            {"focus_fraction": -0.01}, {"detection_dropout": True},
            {"frame_dropout": -0.01},
        ]
        for entry in invalids:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                config(**entry)
        scene = example_scene()
        for case in ({"capture_index": -1}, {"capture_index": 2**32},
                     {"capture_index": True}, {"timestamp_s": float("inf")},
                     {"timestamp_s": -1}, {"timestamp_s": False}):
            with self.subTest(case=case), self.assertRaises(ValueError):
                simulate_sensor(scene, scene.start, config(), **case)
        with self.assertRaises(ValueError):
            simulate_sensor(scene, scene.start, object())

    def test_versioned_input_and_strict_json(self):
        preset, raw = load_sensor_config(PRESET)
        self.assertIn(b"uncalibrated_synthetic", raw)
        self.assertEqual(preset.master_seed, 20261027)
        with tempfile.TemporaryDirectory() as tmp:
            d = json.loads(raw)
            for i, broken in enumerate((
                d | {"calibration_state": "physical_calibrated"},
                d | {"evidence_type": "physical"},
                d | {"width_px": "640"},
                d | {"unexpected": 2},
            )):
                p = Path(tmp) / f"invalid_{i}.json"
                p.write_text(json.dumps(broken), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_sensor_config(p)
            p = Path(tmp) / "duplicated.json"
            p.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}',
                         encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_sensor_config(p)


if __name__ == "__main__":
    unittest.main()
