"""The documented command writes reproducible paired reports and useful errors."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rvi.cli import main

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "simulation/suites/fixture_smoke.json"


class BenchmarkCliTests(unittest.TestCase):
    def test_report_and_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            outputs = [Path(temp) / "nested" / f"report{i}.json" for i in range(2)]
            with redirect_stdout(io.StringIO()):
                for output in outputs:
                    self.assertEqual(main(["benchmark", "--suite", str(SUITE),
                                           "--output", str(output)]), 0)
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
            self.assertEqual(len(json.loads(outputs[0].read_text())["trials"]), 9)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "existing.json"
            output.write_text("keep")
            with redirect_stderr(io.StringIO()) as error, self.assertRaises(SystemExit) as exit:
                main(["benchmark", "--suite", str(SUITE), "--output", str(output)])
            self.assertEqual(exit.exception.code, 2)
            self.assertIn("output already exists", error.getvalue())
            self.assertEqual(output.read_text(), "keep")

    def test_invalid_input_leaves_no_result(self):
        with tempfile.TemporaryDirectory() as temp:
            suite = Path(temp) / "invalid.json"
            suite.write_text('{"evidence_type":"physical"}')
            output = Path(temp) / "output.json"
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exit:
                main(["benchmark", "--suite", str(suite), "--output", str(output)])
            self.assertEqual(exit.exception.code, 2)
            self.assertFalse(output.exists())

    def test_plan_never_overwrites_existing_output_or_scenario(self):
        scenario = ROOT / "simulation/scenarios/inspection_small.json"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_report = root / "prior.json"
            old_report.write_bytes(b"immutable-previous-result")
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
                main(["plan", "--scenario", str(scenario), "--output", str(old_report)])
            self.assertEqual(err.exception.code, 2)
            self.assertEqual(old_report.read_bytes(), b"immutable-previous-result")
            original = root / "input.json"
            original.write_bytes(scenario.read_bytes())
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["plan", "--scenario", str(original), "--output", str(original)])
            self.assertEqual(original.read_bytes(), scenario.read_bytes())
            alias = root / "alias.json"
            alias.symlink_to(original)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["plan", "--scenario", str(original), "--output", str(alias)])
            self.assertEqual(original.read_bytes(), scenario.read_bytes())
            target = root / "new" / "plan.json"
            self.assertEqual(main(["plan", "--scenario", str(original), "--output", str(target)]), 0)
            self.assertEqual(json.loads(target.read_text())["evidence_type"], "synthetic_fixture")

    def test_module_entrypoint_reports_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            completed = subprocess.run(
                [sys.executable, "-m", "rvi", "benchmark", "--suite",
                 "missing-suite.json", "--output", "unused-report.json"],
                capture_output=True, text=True, cwd=temp,
                env=os.environ | {"PYTHONPATH": str(ROOT / "src")})
        self.assertEqual(completed.returncode, 2)
        self.assertIn("error:", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
