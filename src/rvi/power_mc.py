"""Reproducible synthetic family-level Monte Carlo diagnostics for Study 01.

Investigates interval coverage and rejection under declared *artificial*
sampling models. Results never establish field power or preregistration.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
import random
from statistics import NormalDist, fmean, stdev

from .evidence import software_provenance
from .scenarios import read_json

VERSION = "1.0.0"
NORMAL = NormalDist()
DISTRIBUTIONS = ("normal", "student_t5")
MISSINGNESS = ("independent", "family_effect_dependent")


def _number(value: object, key: str, low: float, high: float, *, open_low=False,
            open_high=False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    if value < low or value > high or (open_low and value == low) or (
            open_high and value == high):
        raise ValueError(f"{key} lies outside the allowed range")
    return float(value)


def _integer(value: object, key: str, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{key} must be an integer from {lower} to {upper}")
    return value


def _t_critical(df: int, confidence: float) -> float:
    """Cornish-Fisher approximation to two-sided Student-t quantile, df >= 2.

    A numerical approximation, not an exact Student-t distribution or proof
    of nominal coverage at very small cluster counts.
    """
    z = NORMAL.inv_cdf((1 + confidence) / 2)
    n = float(df)
    return (z + (z**3 + z) / (4 * n)
            + (5*z**5 + 16*z**3 + 3*z) / (96*n*n)
            + (3*z**7 + 19*z**5 + 17*z**3 - 15*z) / (384*n**3))


def _draw(rng: random.Random, distribution: str) -> float:
    if distribution == "normal":
        return rng.gauss(0, 1)
    # Standardized Student t5 with unit variance (5 / (5-2)).
    chi2 = sum(rng.gauss(0, 1)**2 for _ in range(5))
    return rng.gauss(0, 1) / math.sqrt(chi2 / 5) / math.sqrt(5 / 3)


def _scenario(entry: dict) -> dict:
    if not isinstance(entry, dict) or set(entry) != {
            "id", "families", "between_family_sd", "within_family_sd",
            "missing_family_fraction", "family_distribution",
            "missingness_mechanism"}:
        raise ValueError("scenario has invalid or missing fields")
    label = entry["id"]
    if (not isinstance(label, str) or not 1 <= len(label) <= 48 or any(
            c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in label)):
        raise ValueError("invalid scenario identifier")
    n = _integer(entry["families"], "families", 3, 256)
    between = _number(entry["between_family_sd"], "between_family_sd",
                      0, 2, open_low=True)
    within = _number(entry["within_family_sd"], "within_family_sd", 0, 2)
    missing = _number(entry["missing_family_fraction"], "missing_family_fraction",
                      0, .75, open_high=True)
    dist = entry["family_distribution"]
    mech = entry["missingness_mechanism"]
    if dist not in DISTRIBUTIONS or mech not in MISSINGNESS:
        raise ValueError("unknown family distribution or missingness model")
    return {"id": label, "families": n, "between_family_sd": between,
            "within_family_sd": within, "missing_family_fraction": missing,
            "family_distribution": dist, "missingness_mechanism": mech}


def _cell(scenario: dict, *, effect: float, repetitions: int, replicates: int,
          confidence: float, seed: int) -> dict:
    # Independent RNG domain for each scenario and each null/alternative.
    domain = (f"rvi-p01-mc-v1:{seed}:{scenario['id']}:{effect:.17g}:"
              f"{repetitions}:{replicates}").encode("ascii")
    rng = random.Random(int.from_bytes(hashlib.sha256(domain).digest()[:8], "big"))
    stats = {method: {"rejected": 0, "covered": 0, "width_sum": 0.0}
             for method in ("normal_z", "t_approx")}
    estimates = []
    insufficient = 0
    complete_n = []
    for _ in range(repetitions):
        family_means = []
        for _ in range(scenario["families"]):
            shift = scenario["between_family_sd"] * _draw(rng, scenario["family_distribution"])
            p = scenario["missing_family_fraction"]
            if scenario["missingness_mechanism"] == "family_effect_dependent":
                # Missingness depends on latent family signal: intentional bias stress test.
                p = min(.95, p * (1.5 if shift > 0 else .5))
            if rng.random() < p:
                continue
            observations = [effect + shift + scenario["within_family_sd"] * rng.gauss(0, 1)
                            for _ in range(replicates)]
            family_means.append(fmean(observations))
        n = len(family_means)
        complete_n.append(n)
        if n < 3:
            insufficient += 1
            continue
        estimate = fmean(family_means)
        estimates.append(estimate)
        standard_error = stdev(family_means) / math.sqrt(n)
        for method, critical in (("normal_z", NORMAL.inv_cdf((1 + confidence) / 2)),
                                 ("t_approx", _t_critical(n - 1, confidence))):
            half_width = critical * standard_error
            lower, upper = estimate - half_width, estimate + half_width
            stats[method]["rejected"] += lower > 0 or upper < 0
            stats[method]["covered"] += lower <= effect <= upper
            stats[method]["width_sum"] += 2 * half_width
    effective = len(estimates)
    results = {}
    for method, agg in stats.items():
        results[method] = {
            "evaluated": effective,
            "rejection_probability": agg["rejected"] / effective if effective else None,
            "confidence_interval_coverage": agg["covered"] / effective if effective else None,
            "mean_interval_width": agg["width_sum"] / effective if effective else None,
            "rejection_probability_mcse": (
                math.sqrt(agg["rejected"] / effective * (1 - agg["rejected"] / effective)
                          / effective) if effective else None),
            "coverage_mcse": (
                math.sqrt(agg["covered"] / effective * (1 - agg["covered"] / effective)
                          / effective) if effective else None),
        }
    return {
        "true_effect": effect, "requested_repetitions": repetitions,
        "non_estimable_repetitions": insufficient, "estimable_repetitions": effective,
        "mean_observed_families": fmean(complete_n),
        "mean_estimated_effect": fmean(estimates) if effective else None,
        "mean_estimation_bias": fmean(estimates) - effect if effective else None,
        "interval_methods": results,
    }


def analyze_cluster_monte_carlo(spec_path: Path) -> dict:
    """Read an illustrative input specification; never open research holdouts."""
    spec, raw = read_json(Path(spec_path))
    if set(spec) != {
            "schema_version", "study_id", "status", "design",
            "master_seed", "repetitions", "replicates_per_family",
            "confidence_level", "alternative_effect", "scenarios"}:
        raise ValueError("invalid Monte Carlo specification fields")
    if (spec["schema_version"], spec["study_id"], spec["status"],
            spec["design"]) != (VERSION, "01", "illustrative_not_frozen",
                               "paired_family_effect_model"):
        raise ValueError("Monte Carlo input is not an illustrative Study 01 design")
    seed = _integer(spec["master_seed"], "master_seed", 0, 2**64 - 1)
    repetitions = _integer(spec["repetitions"], "repetitions", 100, 5000)
    repeats = _integer(spec["replicates_per_family"], "replicates_per_family", 1, 16)
    confidence = _number(spec["confidence_level"], "confidence_level",
                         .8, .999, open_high=True)
    alternative = _number(spec["alternative_effect"], "alternative_effect",
                          0, 2, open_low=True)
    raw_scenarios = spec["scenarios"]
    if not isinstance(raw_scenarios, list) or not 1 <= len(raw_scenarios) <= 16:
        raise ValueError("expected 1–16 Monte Carlo scenarios")
    scenarios = [_scenario(row) for row in raw_scenarios]
    if len({s["id"] for s in scenarios}) != len(scenarios):
        raise ValueError("scenario ids must be unique")
    if repetitions * sum(s["families"] for s in scenarios) * repeats > 2_000_000:
        raise ValueError("Monte Carlo work exceeds bounded offline budget")
    results = []
    for scenario in scenarios:
        for effect in (0.0, alternative):
            estimate = _cell(scenario, effect=effect, repetitions=repetitions,
                             replicates=repeats, confidence=confidence, seed=seed)
            results.append({"scenario_id": scenario["id"],
                            "effect_condition": "null" if effect == 0.0 else "alternative",
                            **estimate})
    return {
        "schema_version": VERSION, "study_id": "01",
        "status": "illustrative_simulation_not_confirmatory",
        "evidence_type": "simulation", "independent_unit": "geometry_family",
        "design": "paired_family_effect_model",
        "confidence_level": confidence, "repetitions": repetitions,
        "replicates_per_family": repeats, "alternative_effect": alternative,
        "seed": seed, "prng": "python_random_Mersenne_Twister",
        "interval_methods": ["normal_z", "t_approx"],
        "scenarios": scenarios, "results": results,
        "spec_sha256": hashlib.sha256(raw).hexdigest(),
        "source": software_provenance(),
        "limitations": [
            "Simulated paired family contrasts do not represent validated objects or physical sessions.",
            "t_approx uses a Cornish-Fisher quantile approximation; coverage and power are empirical here.",
            "Missing-family stress is conditional on specified synthetic latent effects.",
            "No cross-classified operator/object model, adaptive selection or multiplicity correction.",
            "All simulation draws are exploratory; no sample size, margin or model is preregistered.",
        ],
    }
