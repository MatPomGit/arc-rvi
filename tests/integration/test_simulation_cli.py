"""Simulation command replay, input validation and preserved output files."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from rvi.cli import main

ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / "simulation/worlds/planar_inspection.json"


class SimulationCliTests(unittest.TestCase):
    def test_end_to_end_and_exact_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            outputs = [Path(temp) / "nested" / f"sim{i}.json" for i in range(2)]
            with redirect_stdout(io.StringIO()):
                for output in outputs:
                    self.assertEqual(main(["simulate", "--scene", str(SCENE),
                                           "--output", str(output)]), 0)
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
            result = json.loads(outputs[0].read_text())
            self.assertEqual(result["scene_sha256"], hashlib.sha256(SCENE.read_bytes()).hexdigest())
            self.assertEqual(result["evidence_type"], "simulation")
            self.assertEqual(result["source"]["package_version"],
                             tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"])
            self.assertEqual(result["observations"][1]["requested_pose"]["y"], 1)
            self.assertEqual(result["elapsed_time_s"], 3)

    def test_input_is_never_overwritten(self):
        before = SCENE.read_bytes()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exit:
            main(["simulate", "--scene", str(SCENE), "--output", str(SCENE)])
        self.assertEqual(exit.exception.code, 2)
        self.assertEqual(before, SCENE.read_bytes())

    def test_malformed_scene_reports_error_without_result(self):
        original = json.loads(SCENE.read_text())
        cases = [original | {"evidence_type": "physical"},
                 original | {"motion": original["motion"] | {"linear_speed_m_s": 0}},
                 original | {"camera": original["camera"] | {"max_range_m": True}},
                 original | {"route": "not a route"},
                 original | {"unexpected": 1},
                 original | {"obstacles": [None]},
                 original | {"start": {"x": "0", "y": 0, "yaw_rad": 0}}]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for case in cases:
                with self.subTest(case=case):
                    input = root / "invalid.json"
                    output = root / "output.json"
                    input.write_text(json.dumps(case))
                    with redirect_stderr(io.StringIO()) as error, self.assertRaises(SystemExit) as exit:
                        main(["simulate", "--scene", str(input), "--output", str(output)])
                    self.assertEqual(exit.exception.code, 2)
                    self.assertNotIn("Traceback", error.getvalue())
                    self.assertFalse(output.exists())
