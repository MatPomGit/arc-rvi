"""Paired policies receive identical geometry and retain actual acquired coverage."""

from contextlib import redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest

from rvi.adapters.simulator import load_scene
from rvi.benchmark import evaluate_simulation_policy, run_benchmark
from rvi.cli import main
from rvi.interfaces import CameraPose

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
