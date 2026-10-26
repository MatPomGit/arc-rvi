"""Integration contract: generated worlds load and run with existing simulator."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from rvi.adapters.simulator import load_scene, PlanarSimulator
from rvi.benchmark import run_benchmark
from rvi.conditions import generate_conditions

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "simulation/conditions/study01_pilot.json"


class GeneratedScenesIntegrationTests(unittest.TestCase):
    def test_generated_scenes_are_model_inputs_and_paired(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "generated"
            manifest = generate_conditions(SPEC, output)
            for record in manifest["scenes"]:
                scene, _ = load_scene(output / record["path"])
                simulator = PlanarSimulator(scene)
                self.assertEqual(simulator.scene.identifier, record["scene_id"])
                observed = simulator.visible_patches(scene.route[0])
                if record["condition"] == "nominal":
                    self.assertIn("surface_01", observed)
                else:
                    self.assertNotIn("surface_01", observed)
            for partition, item in manifest["suites"].items():
                result = run_benchmark(output / item["path"])
                self.assertEqual(len(result["trials"]), 36)
                self.assertEqual(len(result["scenes"]), 12)
                self.assertEqual(result["visibility_access"], "known_geometry_oracle")
                for method in result["methods"]:
                    rows = [row for row in result["trials"] if row["method"] == method]
                    self.assertEqual(len(rows), 12)
                    self.assertEqual(len({row["scene_id"] for row in rows}), 12)


if __name__ == "__main__":
    unittest.main()
