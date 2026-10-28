"""Analytic checks for fixture-only horizontal foot-support preflight."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from math import isclose
from pathlib import Path
import tempfile
import unittest

from rvi.cli import main
from rvi.support import inspect_static_support, inspect_support_file


def fixture() -> dict:
    return {
        "schema_version": "1.0.0",
        "terrain_class": "flat_horizontal",
        "com_projection_xy_m": [0.0, 0.0],
        "required_margin_m": 0.05,
        "contacts": [
            {
                "id": "foot_a", "height_m": 0.0, "contact_state": "assumed",
                "footprint_xy_m": [
                    [-0.1, -0.2], [0.1, -0.2],
                    [0.1, -0.1], [-0.1, -0.1],
                ],
            },
            {
                "id": "foot_b", "height_m": 0.0, "contact_state": "assumed",
                "footprint_xy_m": [
                    [-0.1, 0.1], [0.1, 0.1],
                    [0.1, 0.2], [-0.1, 0.2],
                ],
            },
        ],
    }


class StaticSupportTests(unittest.TestCase):
    def test_analytic_two_foot_support_and_boundary_margin(self):
        spec = fixture()
        report = inspect_static_support(spec)
        self.assertEqual(report["status"], "geometric_candidate_only")
        self.assertTrue(isclose(report["signed_support_margin_m"], 0.1,
                                rel_tol=0, abs_tol=1e-12))
        self.assertEqual(len(report["support_polygon_xy_m"]), 4)
        self.assertEqual(report["evidence_type"], "synthetic_fixture")
        self.assertEqual(report["dynamic_balance"], "not_modelled")
        self.assertEqual(report["robot_adapter"], "not_configured")
        self.assertEqual(report, inspect_static_support(spec))
        reverse = deepcopy(spec)
        reverse["contacts"][0]["footprint_xy_m"].reverse()
        self.assertEqual(report, inspect_static_support(reverse))

        spec["required_margin_m"] = 0.11
        self.assertEqual(inspect_static_support(spec)["status"],
                         "insufficient_static_margin")
        spec["required_margin_m"] = 0
        spec["com_projection_xy_m"] = [0.1, 0]
        self.assertEqual(inspect_static_support(spec)["status"],
                         "insufficient_static_margin")
        spec["com_projection_xy_m"] = [0.25, 0]
        outside = inspect_static_support(spec)
        self.assertEqual(outside["status"], "outside_support_projection")
        self.assertTrue(isclose(outside["signed_support_margin_m"], -0.15,
                                rel_tol=0, abs_tol=1e-12))

    def test_one_foot_and_assumed_support_gap(self):
        spec = fixture()
        spec["contacts"] = spec["contacts"][:1]
        spec["com_projection_xy_m"] = [0.0, -0.15]
        spec["required_margin_m"] = 0.04
        report = inspect_static_support(spec)
        self.assertEqual(report["status"], "geometric_candidate_only")
        self.assertTrue(isclose(report["signed_support_margin_m"], 0.05,
                                rel_tol=0, abs_tol=1e-12))
        spec["com_projection_xy_m"] = [0, 0]
        self.assertEqual(inspect_static_support(spec)["status"],
                         "outside_support_projection")

    def test_unsupported_terrain_and_unknown_contacts_fail_closed(self):
        for terrain in ("steps", "slope", "loose", "unknown"):
            spec = fixture()
            spec["terrain_class"] = terrain
            with self.subTest(terrain=terrain):
                result = inspect_static_support(spec)
                self.assertEqual(result["status"], "terrain_model_unsupported")
                self.assertIsNone(result["signed_support_margin_m"])
                self.assertIsNone(result["support_polygon_xy_m"])
        spec = fixture()
        spec["contacts"][1]["height_m"] = 0.12
        self.assertEqual(inspect_static_support(spec)["status"],
                         "noncoplanar_contact_unsupported")
        spec = fixture()
        spec["contacts"][1]["contact_state"] = "unknown"
        self.assertEqual(inspect_static_support(spec)["status"],
                         "contact_state_unknown")
        self.assertIsNone(inspect_static_support(spec)["support_polygon_xy_m"])

    def test_reject_nonconvex_duplicate_or_degenerate_support(self):
        shapes = [
            [[0, 0], [1, 1], [0, 1], [1, 0]],
            [[0, 0], [2, 0], [0.5, 0.2], [2, 2], [0, 2]],
            [[0, 0], [1, 0], [1, 0], [0, 1]],
            [[0, 0], [1, 0], [2, 0]],
        ]
        for polygon in shapes:
            spec = fixture()
            spec["contacts"][0]["footprint_xy_m"] = polygon
            with self.subTest(polygon=polygon), self.assertRaises(ValueError):
                inspect_static_support(spec)

    def test_schema_bounds_and_nonfinite_rejected(self):
        examples = [
            ("terrain_class", "stairs_unrecognized"),
            ("schema_version", "2.0.0"),
            ("required_margin_m", -0.01),
            ("required_margin_m", float("nan")),
            ("required_margin_m", True),
            ("com_projection_xy_m", [float("inf"), 0]),
            ("com_projection_xy_m", [0]),
            ("contacts", []),
            ("contacts", [fixture()["contacts"][0]] * 3),
        ]
        for key, value in examples:
            spec = fixture()
            spec[key] = value
            with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                inspect_static_support(spec)
        spec = fixture()
        spec["contacts"][1]["id"] = "foot_a"
        with self.assertRaisesRegex(ValueError, "distinct"):
            inspect_static_support(spec)
        spec = fixture()
        spec["contacts"][0]["contact_state"] = "measured_verified"
        with self.assertRaises(ValueError):
            inspect_static_support(spec)
        spec = fixture()
        spec["contacts"][0]["friction_coefficient"] = 1.0
        with self.assertRaises(ValueError):
            inspect_static_support(spec)

    def test_file_hash_cli_non_destructive_and_no_robot_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "fixture.json"
            raw = (json.dumps(fixture(), sort_keys=True) + "\n").encode()
            path.write_bytes(raw)
            report = inspect_support_file(path)
            self.assertEqual(report["source_sha256"], sha256(raw).hexdigest())
            out = root / "report.json"
            command = ["stance", "--spec", str(path), "--output", str(out)]
            with redirect_stdout(StringIO()):
                self.assertEqual(main(command), 0)
            self.assertEqual(json.loads(out.read_text()), report)
            original = out.read_bytes()
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                main(command)
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(out.read_bytes(), original)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(["stance", "--spec", str(path), "--output", str(path)])
            self.assertEqual(path.read_bytes(), raw)
            link = root / "alias.json"
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "non-symlinked"):
                inspect_support_file(link)
            path.write_bytes(b'{"required_margin_m": NaN}')
            with self.assertRaises(ValueError):
                inspect_support_file(path)
            path.write_bytes(b"X" * 65537)
            with self.assertRaisesRegex(ValueError, "byte limit"):
                inspect_support_file(path)



def spatial_fixture() -> dict:
    """Two separate feet share the analytic plane z = 0.2*x, metres."""
    original = fixture()
    return {
        "schema_version": "1.1.0",
        "terrain_class": "slope",
        "contacts": [
            {
                "id": c["id"], "contact_state": "assumed",
                "footprint_xyz_m": [[x, y, 0.2 * x]
                                   for x, y in c["footprint_xy_m"]],
            }
            for c in original["contacts"]
        ],
        "com_xyz_m": [0.0, 0.0, 0.9],
        "required_margin_m": 0.05,
    }


class SpatialSupportTests(unittest.TestCase):
    def test_sloped_plane_and_gravity_projection_analytic(self):
        from math import atan, degrees

        report = inspect_static_support(spatial_fixture())
        self.assertEqual(report["schema_version"], "1.1.0")
        self.assertEqual(report["status"], "geometric_candidate_only")
        self.assertEqual(report["margin_basis"], "horizontal_xy_projection_m")
        self.assertAlmostEqual(report["plane_slope_deg"],
                               degrees(atan(0.2)), places=10)
        self.assertAlmostEqual(report["signed_support_margin_m"], 0.1)
        self.assertAlmostEqual(report["support_plane_z_at_com_m"], 0.0)
        self.assertAlmostEqual(report["com_height_above_plane_m"], 0.9)
        self.assertAlmostEqual(report["plane_residual_max_m"], 0.0, places=10)
        self.assertEqual(report["friction_force_feasibility"], "not_modelled")
        self.assertEqual(report["physical_robot_validation"], "not_performed")
        reverse = spatial_fixture()
        reverse["contacts"][0]["footprint_xyz_m"].reverse()
        self.assertEqual(report, inspect_static_support(reverse))

    def test_flat_spatial_agrees_with_legacy_polygon(self):
        spatial = spatial_fixture()
        spatial["terrain_class"] = "flat_horizontal"
        for c in spatial["contacts"]:
            for vertex in c["footprint_xyz_m"]:
                vertex[2] = 0.0
        report = inspect_static_support(spatial)
        legacy = inspect_static_support(fixture())
        self.assertEqual(report["status"], legacy["status"])
        self.assertEqual(report["support_polygon_xy_m"],
                         legacy["support_polygon_xy_m"])
        self.assertAlmostEqual(report["signed_support_margin_m"],
                               legacy["signed_support_margin_m"])
        self.assertEqual(report["plane_slope_deg"], 0.0)

    def test_sloped_nonplanar_or_unknown_support_fail_closed(self):
        for terrain in ("steps", "loose", "unknown"):
            case = spatial_fixture()
            case["terrain_class"] = terrain
            result = inspect_static_support(case)
            self.assertEqual(result["status"], "terrain_model_unsupported")
            self.assertIsNone(result["signed_support_margin_m"])
            self.assertIsNone(result["support_polygon_xy_m"])

        case = spatial_fixture()
        case["contacts"][1]["footprint_xyz_m"][0][2] += 0.02
        result = inspect_static_support(case)
        self.assertEqual(result["status"], "noncoplanar_contact_unsupported")
        self.assertIsNone(result["support_polygon_xy_m"])
        case = spatial_fixture()
        case["contacts"][1]["contact_state"] = "unknown"
        result = inspect_static_support(case)
        self.assertEqual(result["status"], "contact_state_unknown")
        self.assertIsNone(result["signed_support_margin_m"])

        case = spatial_fixture()
        case["terrain_class"] = "flat_horizontal"
        self.assertEqual(inspect_static_support(case)["status"],
                         "terrain_geometry_mismatch")
        case = spatial_fixture()
        case["com_xyz_m"][2] = -0.1
        result = inspect_static_support(case)
        self.assertEqual(result["status"], "com_not_above_support_plane")
        self.assertIsNone(result["signed_support_margin_m"])
        case = spatial_fixture()
        case["com_xyz_m"][0] = 0.3
        result = inspect_static_support(case)
        self.assertEqual(result["status"], "outside_support_projection")
        self.assertLess(result["signed_support_margin_m"], 0)

    def test_spatial_field_schema_and_geometry_guards(self):
        case = spatial_fixture()
        case["com_xyz_m"] = [0.0, 0.0]
        with self.assertRaises(ValueError):
            inspect_static_support(case)
        case = spatial_fixture()
        case["contacts"][0]["footprint_xyz_m"][0][2] = float("nan")
        with self.assertRaises(ValueError):
            inspect_static_support(case)
        case = spatial_fixture()
        case["contacts"][0]["footprint_xyz_m"][0] = [1, 2]
        with self.assertRaises(ValueError):
            inspect_static_support(case)
        case = spatial_fixture()
        case["contacts"][0]["friction_guess"] = 0.8
        with self.assertRaises(ValueError):
            inspect_static_support(case)
        case = spatial_fixture()
        case["required_margin_m"] = -0.1
        with self.assertRaises(ValueError):
            inspect_static_support(case)
        case = spatial_fixture()
        case["contacts"][1]["id"] = "foot_a"
        with self.assertRaises(ValueError):
            inspect_static_support(case)
        case = spatial_fixture()
        case["contacts"][0]["footprint_xyz_m"] = [
            [0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0],
        ]
        with self.assertRaises(ValueError):
            inspect_static_support(case)

    def test_spatial_json_cli_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "sloped_contact.json"
            raw = (json.dumps(spatial_fixture(), sort_keys=True) + "\n").encode()
            path.write_bytes(raw)
            direct = inspect_support_file(path)
            self.assertEqual(direct["source_sha256"], sha256(raw).hexdigest())
            destination = root / "readout.json"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["stance", "--spec", str(path),
                                       "--output", str(destination)]), 0)
            self.assertEqual(json.loads(destination.read_text()), direct)
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(["stance", "--spec", str(path), "--output", str(destination)])


if __name__ == "__main__":
    unittest.main()
