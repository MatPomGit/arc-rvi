"""Image-derived colour cues are only hints and must abstain on two red cars."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from rvi.vehicle_colour_cues import propose_colour_targets


def ppm(pixels):
    return b"P6\n4 2\n255\n" + bytes(v for rgb in pixels for v in rgb)


def pgm(ids):
    return b"P5\n4 2\n255\n" + bytes(ids)


def put(folder, name, data):
    (folder / name).write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


class ColourGroundingTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mask_left = put(self.root, "left.pgm", pgm([255,255,0,0,255,255,0,0]))
        self.mask_right = put(self.root, "right.pgm", pgm([0,0,255,255,0,0,255,255]))
        self.image = put(self.root, "cars.ppm", ppm(
            [(220,40,40),(220,40,40),(40,40,220),(40,40,220)]*2))
        self.spec = {
            "schema_version": 1,
            "request": {
                "utterance_id": "human-command-1",
                "observation_frame_id": "camera-frame-1",
                "requested_colour": "red",
            },
            "image": self.image,
            "policy": {
                "minimum_chroma": 30, "minimum_intensity": 40,
                "maximum_intensity": 245, "minimum_mask_pixels": 4,
                "minimum_usable_fraction": .5,
                "minimum_matching_fraction": .8,
            },
            "candidates": [
                {
                    "vehicle_instance_id": "car-left",
                    "mask_annotation_id": "anon-left",
                    "annotation_origin": "fixture_only",
                    "car_body_mask": self.mask_left,
                },
                {
                    "vehicle_instance_id": "car-right",
                    "mask_annotation_id": "anon-right",
                    "annotation_origin": "fixture_only",
                    "car_body_mask": self.mask_right,
                },
            ],
        }

    def test_checked_in_colour_scene_hashes_and_read_only_cli(self):
        repo = Path(__file__).resolve().parents[1]
        root = repo / "simulation/suites"
        manifest = root / "vehicle_colour_two_cars_manifest.json"
        spec = json.loads(manifest.read_text(encoding="utf-8"))
        result = propose_colour_targets(spec, root)
        self.assertEqual(result["candidate_instance_ids"], ["synthetic-left-car"])
        self.assertFalse(result["identity_confirmed"])
        p = subprocess.run([
            sys.executable, str(repo / "scripts/propose_vehicle_colour_targets.py"),
            "--manifest", str(manifest), "--data-root", str(root)
        ], capture_output=True, text=True, check=False, cwd=repo)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["status"], "single_unverified_colour_candidate")

    def test_one_red_car_is_a_hint_not_authorized_binding(self):
        result = propose_colour_targets(self.spec, self.root)
        self.assertEqual(result["status"], "single_unverified_colour_candidate")
        self.assertEqual(result["candidate_instance_ids"], ["car-left"])
        self.assertFalse(result["identity_confirmed"])
        self.assertFalse(result["safe_to_start_physical_inspection"])
        self.assertFalse(result["part_recognized"])

    def test_two_red_cars_are_ambiguous(self):
        self.spec["image"] = put(self.root, "both_red.ppm", ppm(
            [(220,40,40)]*8))
        result = propose_colour_targets(self.spec, self.root)
        self.assertEqual(result["status"], "ambiguous_multiple_colour_candidates")
        self.assertEqual(result["candidate_instance_ids"], ["car-left", "car-right"])
        self.assertFalse(result["identity_confirmed"])

    def test_requested_blue_returns_other_candidate(self):
        self.spec["request"]["requested_colour"] = "blue"
        result = propose_colour_targets(self.spec, self.root)
        self.assertEqual(result["candidate_instance_ids"], ["car-right"])

    def test_saturated_glare_pixels_are_excluded_not_red(self):
        self.spec["image"] = put(self.root, "glare.ppm", ppm(
            [(255,255,255),(255,255,255),(40,40,220),(40,40,220)]*2))
        self.assertEqual(propose_colour_targets(self.spec, self.root)["candidate_instance_ids"], [])

    def test_unobserved_colour_does_not_claim_target_absence(self):
        self.spec["request"]["requested_colour"] = "green"
        result = propose_colour_targets(self.spec, self.root)
        self.assertEqual(result["status"], "no_supported_colour_candidate")
        self.assertFalse(result["identity_confirmed"])

    def test_masks_cannot_bind_to_wrong_image_dimensions(self):
        bad = deepcopy(self.spec)
        bad["candidates"][0]["car_body_mask"] = put(self.root, "small.pgm", b"P5\n1 1\n255\n\xff")
        with self.assertRaisesRegex(ValueError, "dimensions differ"):
            propose_colour_targets(bad, self.root)

    def test_source_hash_cannot_be_silently_replaced(self):
        bad = deepcopy(self.spec)
        bad["image"]["sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            propose_colour_targets(bad, self.root)

    def test_duplicate_vehicle_id_and_unbounded_candidates_fail(self):
        bad = deepcopy(self.spec)
        bad["candidates"][1]["vehicle_instance_id"] = "car-left"
        with self.assertRaisesRegex(ValueError, "duplicate vehicle"):
            propose_colour_targets(bad, self.root)
        bad = deepcopy(self.spec)
        bad["candidates"] = bad["candidates"]*17
        with self.assertRaisesRegex(ValueError, "exceeds 32"):
            propose_colour_targets(bad, self.root)

    def test_unsupported_colour_and_invalid_threshold_rejected(self):
        bad = deepcopy(self.spec)
        bad["request"]["requested_colour"] = "metallic silver"
        with self.assertRaisesRegex(ValueError, "supported colour"):
            propose_colour_targets(bad, self.root)
        bad = deepcopy(self.spec)
        bad["policy"]["minimum_matching_fraction"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite fraction"):
            propose_colour_targets(bad, self.root)

    def test_masked_pixels_cannot_use_inferred_background_colour(self):
        bad = deepcopy(self.spec)
        bad["candidates"][0]["car_body_mask"] = put(self.root, "empty.pgm", pgm([0]*8))
        result = propose_colour_targets(bad, self.root)
        self.assertEqual(result["candidate_instance_ids"], [])
        self.assertEqual(result["ranked_evidence"][0]["mask_pixels"], 0)


if __name__ == "__main__":
    unittest.main()
