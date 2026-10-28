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


if __name__ == "__main__":
    unittest.main()
