"""Negative tests for serialized decision population integrity."""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from rvi.decision_population import base_scenes, characterize_base, _summarize
from rvi.oracle import exact_oracle
from rvi.adapters.simulator import load_scene
from tempfile import TemporaryDirectory


SPEC = importlib.util.spec_from_file_location(
    "population_verifier",
    Path(__file__).resolve().parents[1] / "scripts/verify_decision_population.py",
)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class PopulationVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A single canonical base isolates the rejection paths cheaply.
        cls.base = next(base_scenes())
        family, n, fov, obstacle, scene = cls.base
        row = dict(characterize_base(scene), family=family,
                   candidate_count=n, fov_deg=fov, central_obstacle=obstacle)
        cls.report = json.loads(json.dumps({
            "schema_version": "1.0.0", "study_id": "01",
            "evidence_type": "simulation",
            "stage": "exploratory_not_confirmatory",
            "partition": "development_decision",
            "independent_unit": "geometry_family",
            "design": "radial_decision_structure_v1",
            "seed": verifier.SEED, "family_count": verifier.FAMILY_COUNT,
            "selection": "none_retain_all", "policy_evaluations": 0,
            "reference_budget_s": verifier.REFERENCE_BUDGET_S,
            "scene_hash_encoding": "sorted compact UTF-8 JSON",
            "rows": [row],
        }))
        cls.summarize(cls.report)

    @staticmethod
    def summarize(report):
        rows = report["rows"]
        row = rows[0]
        report["summary"] = _summarize(rows)
        for key, field in (("by_family", "family"),
                           ("by_candidate_count", "candidate_count"),
                           ("by_fov_deg", "fov_deg"),
                           ("by_obstacle", "central_obstacle")):
            report[key] = {str(row[field]).lower(): _summarize(rows)}
        report["by_budget_ratio"] = {
            str(b): _summarize([dict(row, cases=[c for c in row["cases"]
                                               if c["budget_ratio"] == b])])
            for b in verifier.BUDGET_RATIOS
        }

    def verify(self, report):
        with patch.object(verifier, "base_scenes", return_value=[self.base]):
            verifier.verify(report)

    def rehash(self, case):
        raw = json.dumps(case["scene"], sort_keys=True,
                         separators=(",", ":"), allow_nan=False)
        case["scene_sha256"] = sha256(raw.encode("utf-8")).hexdigest()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "scene.json"
            path.write_text(raw, encoding="utf-8")
            scene, _ = load_scene(path)
            case["oracle"] = exact_oracle(scene)

    def test_valid_serialized_report(self):
        self.verify(deepcopy(self.report))

    def test_metadata(self):
        for key in ("seed", "partition", "evidence_type", "stage",
                    "independent_unit", "design", "schema_version",
                    "study_id", "selection", "scene_hash_encoding",
                    "reference_budget_s", "family_count", "policy_evaluations"):
            with self.subTest(key=key):
                report = deepcopy(self.report)
                report[key] = "corrupted"
                with self.assertRaisesRegex(ValueError, "metadata mismatch"):
                    self.verify(report)

    def test_coordinated_feature_and_summary_change(self):
        report = deepcopy(self.report)
        report["rows"][0]["features"]["minimum_cover_views_without_motion"] = 99
        self.summarize(report)
        with self.assertRaisesRegex(ValueError, "structural features mismatch"):
            self.verify(report)

    def test_budget_reference_and_hash_change(self):
        report = deepcopy(self.report)
        case = report["rows"][0]["cases"][0]
        case["budget_reference_s"] *= 1.2
        case["scene"]["motion"]["max_time_s"] = (
            case["budget_reference_s"] * case["budget_ratio"])
        self.rehash(case)
        self.summarize(report)
        with self.assertRaisesRegex(ValueError, "budget reference mismatch"):
            self.verify(report)

    def test_reference_type(self):
        report = deepcopy(self.report)
        report["rows"][0]["cases"][0]["budget_reference_type"] = "invalid"
        with self.assertRaisesRegex(ValueError, "budget reference mismatch"):
            self.verify(report)

    def test_nonbudget_motion_and_hash_change(self):
        report = deepcopy(self.report)
        case = report["rows"][0]["cases"][0]
        motion = case["scene"]["motion"]
        key = next(k for k in motion if k != "max_time_s")
        motion[key] *= 1.1
        self.rehash(case)
        self.summarize(report)
        with self.assertRaisesRegex(ValueError, "complete scene mismatch"):
            self.verify(report)
