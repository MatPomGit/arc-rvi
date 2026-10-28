"""Bounded real-image ROI photometric proxy tests (all test pixels synthetic)."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from rvi.vehicle_image_quality import analyze_capture, compare_pair, _netpbm


POLICY = {
    "white_channel_clip_threshold": 250,
    "bright_luma_threshold": 235,
    "neutral_channel_spread_max": 25,
    "dark_luma_threshold": 15,
    "max_white_clipped_fraction": 0.25,
    "max_bright_neutral_fraction": 0.25,
    "max_dark_fraction": 0.5,
    "min_roi_pixels": 4,
}


def p6(width, height, rgb):
    return f"P6\n{width} {height}\n255\n".encode() + bytes(rgb)


def p5(width, height, mono):
    return f"P5\n{width} {height}\n255\n".encode() + bytes(mono)


def p3(width, height, rgb):
    return (f"P3\n# Synthetic pixels only\n{width} {height}\n255\n"
            + " ".join(map(str, rgb)) + "\n").encode()


def p2(width, height, mono):
    return (f"P2\n{width} {height}\n255\n"
            + " ".join(map(str, mono)) + "\n").encode()


def write(root: Path, filename: str, raw: bytes):
    (root / filename).write_bytes(raw)
    return {"path": filename, "sha256": hashlib.sha256(raw).hexdigest()}


class VehicleImageQualityTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # 4x4 RGB image, independently annotated 2x2 bumper region.
        # The rest of the image is bright, so whole-image metrics are misleading.
        self.mask = write(self.root, "part.pgm", p5(4, 4, [
            255, 255, 0, 0,
            255, 255, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0,
        ]))
        base = [(250, 251, 255)] * 16
        for j in (0, 1, 4, 5):
            base[j] = (45, 58, 63)
        for j in (0, 1, 4):
            base[j] = (255, 255, 255)
        before = [v for rgb in base for v in rgb]
        base[0] = base[1] = base[4] = (45, 58, 63)
        after = [v for rgb in base for v in rgb]
        self.before = write(self.root, "before.ppm", p6(4, 4, before))
        self.after = write(self.root, "after.ppm", p6(4, 4, after))
        self.a = self.spec(self.before, "obs-before")
        self.b = self.spec(self.after, "obs-after")

    def spec(self, image, obs):
        return {
            "schema_version": 1,
            "image": image,
            "roi_mask": self.mask,
            "association": {
                "vehicle_instance_id": "vehicle-001",
                "part_label": "rear_bumper",
                "slot_id": "rear-bumper-left",
                "observation_id": obs,
                "annotation_id": "anon-operator-part-mask",
                "annotation_origin": "human-drawn-offline",
            },
            "photometric_policy": deepcopy(POLICY),
        }

    def test_before_glare_proxy_rejected_and_after_proxy_passes(self):
        a = analyze_capture(self.a, self.root)
        b = analyze_capture(self.b, self.root)
        self.assertEqual(a["roi_pixels"], 4)
        self.assertEqual(a["metrics"]["white_clipped_fraction"], .75)
        self.assertEqual(a["gate"], "photometric_proxy_reject")
        self.assertIn("white_channel_clipping_proxy", a["reasons"])
        self.assertEqual(b["gate"], "photometric_proxy_pass")
        self.assertEqual(b["metrics"]["white_clipped_fraction"], 0)
        self.assertFalse(b["physical_robot_evidence"])
        self.assertEqual(b["focus_and_defect_visibility"], "not_assessed")

    def test_pair_is_descriptive_and_not_identity_verified(self):
        result = compare_pair(self.a, self.b, self.root)
        self.assertEqual(result["after_minus_before"]["white_clipped_fraction"], -.75)
        self.assertFalse(result["causal_recovery_effect"])
        self.assertFalse(result["calibrated_specular_reflection"])
        self.assertEqual(result["before"]["vehicle_and_part_identity"],
                         "declared_annotation_only_not_model_verified")

    def test_matching_mask_does_not_mean_vehicle_was_recognized(self):
        s = deepcopy(self.a)
        s["association"]["vehicle_instance_id"] = "invented"
        r = analyze_capture(s, self.root)
        self.assertEqual(r["association"]["vehicle_instance_id"], "invented")
        self.assertNotEqual(r["vehicle_and_part_identity"], "verified")

    def test_background_highlights_excluded_by_mask(self):
        b = analyze_capture(self.b, self.root)
        self.assertEqual(b["metrics"]["white_clipped_fraction"], 0)
        self.assertEqual(b["roi_fraction_of_frame"], .25)

    def test_image_hash_check_prevents_unannounced_file_substitution(self):
        data = bytearray((self.root / "after.ppm").read_bytes())
        data[-1] ^= 1
        (self.root / "after.ppm").write_bytes(data)
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            analyze_capture(self.b, self.root)

    def test_mask_mismatch_and_empty_mask_fail(self):
        bad = deepcopy(self.b)
        bad["roi_mask"] = write(self.root, "small.pgm", p5(2, 2, [255]*4))
        with self.assertRaisesRegex(ValueError, "dimensions disagree"):
            analyze_capture(bad, self.root)
        bad["roi_mask"] = write(self.root, "zero.pgm", p5(4, 4, [0]*16))
        with self.assertRaisesRegex(ValueError, "ROI mask empty"):
            analyze_capture(bad, self.root)

    def test_pair_identity_and_image_mismatch_refused(self):
        other = deepcopy(self.b)
        other["association"]["vehicle_instance_id"] = "other-car"
        with self.assertRaisesRegex(ValueError, "vehicle_instance_id"):
            compare_pair(self.a, other, self.root)
        with self.assertRaisesRegex(ValueError, "share the same image"):
            compare_pair(self.b, deepcopy(self.b), self.root)

    def test_traversal_and_symlink_refused(self):
        bad = deepcopy(self.a)
        bad["image"]["path"] = "../outside.ppm"
        with self.assertRaisesRegex(ValueError, "traversal"):
            analyze_capture(bad, self.root)
        (self.root / "alias.ppm").symlink_to(self.root / "before.ppm")
        bad = deepcopy(self.a)
        bad["image"]["path"] = "alias.ppm"
        with self.assertRaisesRegex(ValueError, "symlink"):
            analyze_capture(bad, self.root)

    def test_ascii_images_and_mask_work_and_binary_whitespace_preserved(self):
        # Binary raster begins with whitespace-valued pixels, which must not
        # be mistaken for additional Netpbm header separators.
        width, height, raw = _netpbm(p5(2, 2, [10, 32, 13, 255]), mask=True)
        self.assertEqual((width, height, raw), (2, 2, bytes([10, 32, 13, 255])))
        mask = write(self.root, "ascii.pgm", p2(4, 4, [255]*16))
        img = write(self.root, "ascii.ppm", p3(4, 4, [45, 58, 63]*16))
        s = self.spec(img, "obs-ascii")
        s["roi_mask"] = mask
        self.assertEqual(analyze_capture(s, self.root)["roi_pixels"], 16)

    def test_unsupported_maxval_and_corrupt_ascii_raster_refused(self):
        with self.assertRaisesRegex(ValueError, "binary Netpbm maxval"):
            _netpbm(b"P5\n2 2\n15\n" + bytes([1,2,3,4]), mask=True)
        with self.assertRaisesRegex(ValueError, "sample exceeds"):
            _netpbm(b"P2\n1 1\n10\n11\n", mask=True)
        with self.assertRaisesRegex(ValueError, "trailing ASCII"):
            _netpbm(b"P2\n1 1\n255\n20 100\n", mask=True)

    def test_committed_pair_fixture_provenance_and_offline_cli(self):
        repo = Path(__file__).resolve().parents[1]
        data_root = repo / "simulation" / "suites"
        manifest = data_root / "vehicle_roi_synthetic_pair.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        result = compare_pair(data["before"], data["after"], data_root)
        self.assertEqual(result["before"]["metrics"]["white_clipped_fraction"], .75)
        self.assertEqual(result["after"]["metrics"]["white_clipped_fraction"], 0.0)
        proc = subprocess.run(
            [sys.executable, str(repo / "scripts" / "audit_vehicle_image_roi.py"),
             "--manifest", str(manifest), "--data-root", str(data_root)],
            cwd=repo, capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        cli_data = json.loads(proc.stdout)
        self.assertEqual(cli_data["after_minus_before"]["white_clipped_fraction"], -.75)

    def test_invalid_thresholds_and_nan_fail(self):
        bad = deepcopy(self.b)
        bad["photometric_policy"]["max_bright_neutral_fraction"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            analyze_capture(bad, self.root)
        bad = deepcopy(self.b)
        bad["photometric_policy"]["min_roi_pixels"] = 0
        with self.assertRaisesRegex(ValueError, "positive bounded"):
            analyze_capture(bad, self.root)


if __name__ == "__main__":
    unittest.main()
