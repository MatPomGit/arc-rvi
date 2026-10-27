"""Paired policies receive identical geometry and retain actual acquired coverage."""

from contextlib import redirect_stdout
from dataclasses import replace
from math import pi
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rvi.adapters.simulator import load_scene
from rvi.benchmark import (evaluate_simulation_policy, evaluate_observation_policy,
                           select_observation_view, run_benchmark)
from rvi.cli import main
from rvi.interfaces import CameraPose
from rvi.perception import load_sensor_config

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / 'simulation/suites/geometric_smoke.json'


class GeometricBenchmarkTests(unittest.TestCase):
    def test_paired_scene_hashes_and_descriptive_denominators(self):
        result = run_benchmark(SUITE)
        self.assertEqual(result['evidence_type'], 'simulation')
        self.assertEqual(result['visibility_access'], 'known_geometry_oracle')
        self.assertEqual(len(result['trials']), 6)
        for scene in result['scenes']:
            rows = [r for r in result['trials'] if r['scene_id'] == scene['scene_id']]
            self.assertEqual(len(rows), 3)
            self.assertEqual({r['scene_sha256'] for r in rows}, {scene['sha256']})
        summary = {r['method']: r for r in result['summary']}
        self.assertEqual(summary['fixed_order']['trial_count'], 2)
        self.assertEqual(summary['fixed_order']['success_count'], 1)
        self.assertEqual(summary['fixed_order']['mean_sampled_surface_coverage'], 0.5)
        self.assertEqual(summary['greedy_distance']['success_count'], 2)
        self.assertEqual(summary['greedy_distance']['mean_elapsed_time_s'], 3)
        self.assertEqual(summary['fixed_order']['failures'], {'time_budget_exceeded': 1})

    def test_budget_case_scores_acquired_views_only(self):
        result = run_benchmark(SUITE)
        rows = {r['method']: r for r in result['trials']
                if r['scene_id'] == 'planar_far_first_budget'}
        self.assertEqual(rows['fixed_order']['covered_patch_ids'], [])
        self.assertEqual(rows['fixed_order']['observations'][0]['visible_patch_ids'], ())
        self.assertEqual(rows['fixed_order']['elapsed_time_s'], 0)
        self.assertEqual(rows['greedy_distance']['covered_patch_ids'], ['lower', 'upper'])
        self.assertEqual([o['candidate_id'] for o in rows['greedy_distance']['observations']],
                         ['view_000002', 'view_000003'])

    def test_collision_retains_previous_partial_area(self):
        scene, _ = load_scene(ROOT / 'simulation/worlds/planar_inspection.json')
        scene = replace(scene, route=(CameraPose(0, 0, 0), CameraPose(3, 1, 0)))
        result = evaluate_simulation_policy(scene, 'fixed_order')
        self.assertEqual(result['failure_reason'], 'path_collision')
        self.assertEqual(result['sampled_surface_coverage'], 0.25)
        self.assertEqual(result['elapsed_time_s'], 1)
        self.assertEqual(result['travel_distance_m'], 0)

    def test_empty_candidates_and_invalid_method(self):
        scene, _ = load_scene(ROOT / 'simulation/worlds/planar_inspection.json')
        result = evaluate_simulation_policy(replace(scene, route=()), 'greedy_distance')
        self.assertEqual(result['failure_reason'], 'unreachable_regions')
        self.assertEqual(result['sampled_surface_coverage'], 0)
        with self.assertRaises(ValueError):
            evaluate_simulation_policy(scene, 'unknown')

    def test_simulation_suite_cli_replays_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            outputs = [Path(temp) / f'benchmark{i}.json' for i in range(2)]
            with redirect_stdout(io.StringIO()):
                for output in outputs:
                    self.assertEqual(main(['benchmark', '--suite', str(SUITE),
                                           '--output', str(output)]), 0)
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())


    def test_sensor_policy_uses_past_features_only(self):
        choices = [("near", CameraPose(0.1, 0, 0)),
                   ("far_side", CameraPose(0, 2, 0))]
        history = [(CameraPose(0, 0, 0), {
            "status": "captured", "width_px": 640,
            "detections": [{"id": "feature_0001", "u_px": 320,
                            "range_m": 3, "sharpness_proxy": 1}],
        })]
        self.assertEqual(select_observation_view(
            choices, CameraPose(0, 0, 0), history,
            "nearest_pose", pi / 2)[0], "near")
        self.assertEqual(select_observation_view(
            choices, CameraPose(0, 0, 0), history,
            "sensor_parallax", pi / 2)[0], "far_side")
        history[0][1]["detections"] = []
        self.assertEqual(select_observation_view(
            choices, CameraPose(0, 0, 0), history,
            "sensor_parallax", pi / 2)[0], "near")
        with self.assertRaises(ValueError):
            select_observation_view(choices, CameraPose(0, 0, 0),
                                    history, "unknown", pi / 2)

    def test_sensor_benchmark_is_deterministic_with_isolated_evaluator(self):
        sensor = ROOT / "simulation/conditions/sensor_exploratory.json"
        report = run_benchmark(SUITE, sensor)
        self.assertEqual(report, run_benchmark(SUITE, sensor))
        self.assertEqual(report["visibility_access"], "observations_only")
        self.assertEqual(report["stage"], "exploratory_not_confirmatory")
        self.assertEqual(len(report["trials"]), 6)
        self.assertEqual(set(report["methods"]),
                         {"fixed_order", "nearest_pose", "sensor_parallax"})
        for trial in report["trials"]:
            self.assertIn("detected_patch_ids", trial["evaluator"])
            self.assertGreaterEqual(trial["sampled_surface_coverage"], 0)
            self.assertLessEqual(trial["sampled_surface_coverage"], 1)
            for event in trial["observations"]:
                self.assertNotIn("visible_patch_ids", event)
                self.assertNotIn("geometry_references", event)
                if event["policy_observation"] is not None:
                    serialized = json.dumps(event["policy_observation"])
                    self.assertNotIn("patch_id", serialized)
                    self.assertNotIn("oracle", serialized)
        self.assertEqual({r["trial_count"] for r in report["summary"]}, {2})

    def test_sensor_stream_is_paired_per_candidate_not_action_order(self):
        sensor, _ = load_sensor_config(
            ROOT / "simulation/conditions/sensor_exploratory.json")
        scene, _ = load_scene(ROOT / "simulation/worlds/planar_inspection.json")
        measured = {}
        for method in ("fixed_order", "nearest_pose", "sensor_parallax"):
            trial = evaluate_observation_policy(scene, sensor, method)
            for event in trial["observations"]:
                observation = event["policy_observation"]
                if observation is None:
                    continue
                key = event["candidate_id"]
                if key in measured:
                    self.assertEqual(measured[key], observation["detections"])
                measured[key] = observation["detections"]
        self.assertTrue(measured)

    def test_dropout_and_tampered_evaluator_do_not_affect_policy(self):
        sensor, _ = load_sensor_config(
            ROOT / "simulation/conditions/sensor_exploratory.json")
        scene, _ = load_scene(ROOT / "simulation/worlds/planar_inspection.json")
        dropped = evaluate_observation_policy(
            scene, replace(sensor, frame_dropout=1), "sensor_parallax")
        self.assertEqual(dropped["sampled_surface_coverage"], 0)
        self.assertFalse(dropped["coverage_complete"])
        self.assertTrue(any(
            row["geometry_visible"] for event in dropped["evaluator"]["steps"]
            for row in event["geometry_references"]))
        from rvi.perception import simulate_sensor

        def tampered(*args, **kwargs):
            policy, truth = simulate_sensor(*args, **kwargs)
            return policy, dict(truth, geometry_references=[
                dict(row, detected=False) for row in truth["geometry_references"]])

        baseline = evaluate_observation_policy(scene, sensor, "sensor_parallax")
        with patch("rvi.benchmark.simulate_sensor", side_effect=tampered):
            altered = evaluate_observation_policy(scene, sensor, "sensor_parallax")
        self.assertEqual(
            [r["candidate_id"] for r in baseline["observations"]],
            [r["candidate_id"] for r in altered["observations"]])
        self.assertEqual(
            [r["policy_observation"] for r in baseline["observations"]],
            [r["policy_observation"] for r in altered["observations"]])
        self.assertEqual(altered["sampled_surface_coverage"], 0)

    def test_sensor_mode_cli_and_fixture_gate(self):
        sensor = ROOT / "simulation/conditions/sensor_exploratory.json"
        with self.assertRaisesRegex(ValueError, "require a simulation suite"):
            run_benchmark(ROOT / "simulation/suites/fixture_smoke.json", sensor)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "sensor.json"
            args = ["benchmark", "--suite", str(SUITE),
                    "--sensor", str(sensor), "--output", str(output)]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            original = output.read_bytes()
            with self.assertRaises(SystemExit):
                main(args)
            self.assertEqual(output.read_bytes(), original)

    def test_duplicate_or_malformed_suites_are_rejected(self):
        base = {'schema_version': '1.0.0', 'suite_id': 'bad',
                'evidence_type': 'simulation', 'scenes': []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scene = ROOT / 'simulation/worlds/planar_inspection.json'
            (root / 'scene.json').write_bytes(scene.read_bytes())
            cases = [base, base | {'scenes': 'scene.json'},
                     base | {'scenes': ['scene.json', './scene.json']},
                     base | {'schema_version': '2.0.0', 'scenes': ['scene.json']},
                     base | {'unexpected': 1, 'scenes': ['scene.json']}]
            for payload in cases:
                with self.subTest(payload=payload):
                    path = root / 'suite.json'
                    path.write_text(json.dumps(payload))
                    with self.assertRaises(ValueError):
                        run_benchmark(path)
