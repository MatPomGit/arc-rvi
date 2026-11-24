"""Paired RVI-R06 comparison on the complete RVI-R05 development grid."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from math import fsum, isclose
from pathlib import Path
from tempfile import TemporaryDirectory

from .adapters.simulator import load_scene
from .benchmark import METHODS, FUZZY_METHODS, evaluate_simulation_policy
from .decision_population import BUDGET_RATIOS, base_scenes, _hash, _scene_payload
from .oracle import diagnose_trials, summarize_oracle
from .strong_baselines import STRONG_METHODS, evaluate_strong_policy


ALL_METHODS = METHODS + FUZZY_METHODS + STRONG_METHODS


def _summarize(cases):
    result = summarize_oracle(cases)
    for method, summary in result["methods"].items():
        trials = [t for c in cases for t in c["trials"]
                  if t["method"] == method]
        times = [t["full_time_gap_s"] for t in trials
                 if t["full_time_gap_s"] is not None]
        expanded = [t["expanded_transitions"] for t in trials
                    if "expanded_transitions" in t]
        summary["mean_full_time_gap_s"] = fsum(times) / len(times) if times else None
        summary["mean_expanded_transitions"] = (
            fsum(expanded) / len(expanded) if expanded else None)
    return result


def compare_decision_population(path: Path) -> dict:
    """Read the fixed structural report; validate every scene and oracle."""
    if any("holdout" in p.lower() or "confirm" in p.lower()
           for p in path.resolve().parts):
        raise ValueError("development comparison refuses held-out paths")
    raw = path.read_bytes()
    report = json.loads(raw)
    if (report["schema_version"], report["stage"], report["partition"],
        report["design"], report["selection"], report["policy_evaluations"]) != (
            "1.0.0", "exploratory_not_confirmatory", "development_decision",
            "radial_decision_structure_v1", "none_retain_all", 0):
        raise ValueError("not the RVI-R05 development population")

    expected = {s.identifier: (f, n, v, o, s)
                for f, n, v, o, s in base_scenes()}
    seen = set()
    cases = []
    with TemporaryDirectory() as directory:
        scene_file = Path(directory) / "scene.json"
        for row in report["rows"]:
            identifier = row["scene_id"]
            if identifier not in expected or identifier in seen:
                raise ValueError("unexpected or duplicate base scene")
            seen.add(identifier)
            family, n, fov, obstacle, base = expected[identifier]
            if (row["family"], row["candidate_count"], row["fov_deg"],
                row["central_obstacle"]) != (family, n, fov, obstacle):
                raise ValueError("base factor mismatch")
            if [c["budget_ratio"] for c in row["cases"]] != list(BUDGET_RATIOS):
                raise ValueError("incomplete budget grid")
            for case in row["cases"]:
                payload = case["scene"]
                if _hash(payload) != case["scene_sha256"]:
                    raise ValueError("scene hash mismatch")
                scene_file.write_text(json.dumps(payload, allow_nan=False),
                                      encoding="utf-8")
                scene, _ = load_scene(scene_file)
                ratio = case["budget_ratio"]
                expected_scene = replace(
                    base, identifier=f"{identifier}_r{round(ratio * 100):03d}",
                    motion=replace(base.motion,
                                   max_time_s=case["budget_reference_s"] * ratio))
                if _scene_payload(scene) != _scene_payload(expected_scene):
                    raise ValueError("unexpected scene geometry or budget")

                trials = [evaluate_simulation_policy(scene, method)
                          for method in METHODS + FUZZY_METHODS]
                trials += [evaluate_strong_policy(scene, method)
                           for method in STRONG_METHODS]
                diagnostic = diagnose_trials(scene, trials)
                recorded = case["oracle"]
                if any(diagnostic[k] != value for k, value in recorded.items()):
                    raise ValueError("oracle result differs from structural report")
                for trial in trials:
                    gap = (trial["elapsed_time_s"] - diagnostic["full_min_time_s"]
                           if trial["status"] == "completed" else None)
                    if gap is not None and gap < 0 and not isclose(
                            gap, 0, rel_tol=0, abs_tol=1e-10):
                        raise ValueError("policy time below exact optimum")
                    trial["full_time_gap_s"] = max(0., gap) if gap is not None else None
                cases.append(dict(diagnostic, family=family, budget_ratio=ratio,
                                  scene_sha256=case["scene_sha256"], trials=trials))
    if seen != set(expected) or len(cases) != len(expected) * len(BUDGET_RATIOS):
        raise ValueError("incomplete RVI-R05 case matrix")
    return {
        "schema_version": "1.0.0", "study_id": "01",
        "evidence_type": "simulation", "stage": "exploratory_not_confirmatory",
        "partition": "development_decision", "independent_unit": "geometry_family",
        "selection": "none_retain_all", "population_sha256": sha256(raw).hexdigest(),
        "methods": list(ALL_METHODS), "trial_count": len(cases) * len(ALL_METHODS),
        "summary": _summarize(cases),
        "by_family": {f: _summarize([c for c in cases if c["family"] == f])
                      for f in sorted({c["family"] for c in cases})},
        "by_budget_ratio": {str(b): _summarize(
            [c for c in cases if c["budget_ratio"] == b]) for b in BUDGET_RATIOS},
        "cases": cases,
    }
