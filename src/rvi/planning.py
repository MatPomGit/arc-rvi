"""Assumption-driven planning for independent geometry-family samples.

This is a *sensitivity calculation*, not a confirmation protocol or evidence
that the synthetic simulator describes real equipment or objects.
"""

from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path
from statistics import NormalDist, stdev

from .evidence import software_provenance
from .scenarios import read_json

SCHEMA = "1.0.0"
STATUS = "illustrative_not_frozen"
MAX_FAMILIES = 100_000
NORMAL = NormalDist()


def _number(value: object, field: str, *, low: float, high: float,
            lower_strict: bool = False, upper_strict: bool = False) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{field} must be a number, not bool or string")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (value <= low if lower_strict else value < low) or (
            value >= high if upper_strict else value > high):
        raise ValueError(f"{field} must be finite and in the documented range")
    return float(value)


def _positive_int(value: object, field: str, maximum: int) -> int:
    if type(value) is not int or not 2 <= value <= maximum:
        raise ValueError(f"{field} must be an integer from 2 to {maximum}")
    return value


def _power(n: int, sigma: float, effect: float, critical: float) -> float:
    """Normal-model two-sided Wald power, with known family-level sigma."""
    shift = effect * math.sqrt(n) / sigma
    return NORMAL.cdf(-critical - shift) + NORMAL.cdf(shift - critical)


def _scenario(row: dict, *, critical: float, z_power: float, minimum: int,
              target_power: float, half_width: float, effect: float) -> dict:
    if not isinstance(row, dict) or set(row) != {
            "id", "family_effect_sd", "unusable_family_fraction"}:
        raise ValueError("scenario must have id, family_effect_sd, unusable_family_fraction")
    label = row["id"]
    if not isinstance(label, str) or not label or len(label) > 48 or any(
            char not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for char in label):
        raise ValueError("scenario id must be a short lowercase technical identifier")
    sigma = _number(row["family_effect_sd"], "family_effect_sd",
                    low=0.0, high=2.0, lower_strict=True)
    loss = _number(row["unusable_family_fraction"], "unusable_family_fraction",
                   low=0.0, high=0.95, upper_strict=True)
    # Avoid optimistic cluster inflation: sample size is based on between-family
    # SD of the already paired, within-family-averaged contrast.
    n_precision = max(minimum, math.ceil((critical * sigma / half_width) ** 2))
    n_power = max(minimum, math.ceil(((critical + z_power) * sigma / effect) ** 2))
    completed = max(n_precision, n_power)
    if completed > MAX_FAMILIES:
        raise ValueError("scenario requires more than the allowed maximum families")
    while _power(n_power, sigma, effect, critical) + 1e-14 < target_power:
        n_power += 1
        if n_power > MAX_FAMILIES:
            raise ValueError("scenario power calculation exceeds the maximum")
    completed = max(n_precision, n_power)
    planned = math.ceil(completed / (1.0 - loss))
    if planned > MAX_FAMILIES:
        raise ValueError("planned enrolled families exceed the maximum")
    return {
        "id": label, "assumed_family_effect_sd": sigma,
        "assumed_unusable_family_fraction": loss,
        "families_for_normal_ci_precision": n_precision,
        "families_for_normal_power": n_power,
        "required_complete_families": completed,
        "planned_enrolled_families": planned,
        "estimated_two_sided_normal_power_at_complete_n":
            _power(completed, sigma, effect, critical),
        "estimated_ci_half_width_at_complete_n":
            critical * sigma / math.sqrt(completed),
    }


def _pilot_diagnostics(path: Path) -> dict:
    """Report pilot summaries without substituting pilot variability into design."""
    data, raw = read_json(path)
    if (data.get("stage"), data.get("partition"), data.get("evidence_type"),
            data.get("visibility_access"), data.get("independent_unit")) != (
            "exploratory_not_confirmatory", "pilot", "simulation",
            "known_geometry_oracle", "geometry_family"):
        raise ValueError("only exploratory known-geometry pilot summaries are supported")
    rows = data.get("family_effects")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("pilot diagnostics require at least two family aggregates")
    identifiers = []
    effects = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("family"), str) or not row["family"]:
            raise ValueError("malformed pilot family effects")
        identifiers.append(row["family"])
        effects.append(_number(row.get("completion_loss_difference"),
                               "pilot completion effect", low=-2.0, high=2.0))
    if len(set(identifiers)) != len(identifiers) or data.get("families") != len(rows):
        raise ValueError("pilot family identifiers or count are inconsistent")
    return {
        "status": "diagnostic_only_not_used_to_size_confirmation",
        "pilot_summary_sha256": sha256(raw).hexdigest(),
        "family_count": len(rows),
        "observed_model_completion_contrast_sd": stdev(effects),
        "caution": "Small, model-dependent pilot SD cannot justify physical-world sigma.",
    }


def plan_family_sample(spec_path: Path, pilot_summary: Path | None = None) -> dict:
    """Two-sided normal-approximation sensitivity; no data-dependent stopping."""
    spec, raw = read_json(Path(spec_path))
    expected = {"schema_version", "study_id", "planning_status", "estimand",
                "confidence_level", "target_power", "effect_to_detect",
                "target_ci_half_width", "minimum_complete_families", "scenarios"}
    if set(spec) != expected:
        raise ValueError("planning specification has unexpected or missing fields")
    if (spec["schema_version"], spec["study_id"], spec["planning_status"],
            spec["estimand"]) != (SCHEMA, "01", STATUS,
            "difference_in_nominal_to_occluded_completion_loss"):
        raise ValueError("unsupported study, estimand or frozen planning status")
    confidence = _number(spec["confidence_level"], "confidence_level",
                         low=0.8, high=0.999, upper_strict=True)
    power = _number(spec["target_power"], "target_power",
                    low=0.5, high=0.99, upper_strict=True)
    effect = _number(spec["effect_to_detect"], "effect_to_detect",
                     low=0.0, high=2.0, lower_strict=True)
    half_width = _number(spec["target_ci_half_width"], "target_ci_half_width",
                         low=0.0, high=2.0, lower_strict=True)
    minimum = _positive_int(spec["minimum_complete_families"],
                            "minimum_complete_families", MAX_FAMILIES)
    scenarios = spec["scenarios"]
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 20:
        raise ValueError("need 1 to 20 sensitivity scenarios")
    alpha = 1.0 - confidence
    critical = NORMAL.inv_cdf(1.0 - alpha / 2.0)
    z_power = NORMAL.inv_cdf(power)
    calculations = [
        _scenario(row, critical=critical, z_power=z_power, minimum=minimum,
                  target_power=power, half_width=half_width, effect=effect)
        for row in scenarios
    ]
    identifiers = [row["id"] for row in calculations]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("sensitivity scenario IDs must be unique")
    result = {
        "schema_version": SCHEMA, "study_id": "01",
        "status": "illustrative_sensitivity_not_preregistered",
        "evidence_type": "planning_only",
        "independent_unit": "geometry_family",
        "model": "two_sided_normal_wald_known_between_family_sd",
        "endpoint": spec["estimand"],
        "effect_scale": "absolute_fraction_difference_not_percent",
        "confidence_level": confidence, "target_power": power,
        "effect_to_detect": effect, "target_ci_half_width": half_width,
        "minimum_complete_families": minimum,
        "scenario_results": calculations,
        "spec_sha256": sha256(raw).hexdigest(),
        "source": software_provenance(),
        "limitations": [
            "Illustrative known-variance normal approximation; small-sample t and distributional uncertainty not modeled.",
            "Family SD and unusable rates are assumptions, not measured robot or object properties.",
            "Enrolled counts adjust expected complete families only; attrition is stochastic and no guarantee.",
            "Does not account for crossed nuisance effects, model misspecification or multiple testing.",
            "No design is frozen, preregistered, or authorized for physical inference.",
        ],
    }
    if pilot_summary is not None:
        result["pilot_diagnostics"] = _pilot_diagnostics(Path(pilot_summary))
    return result
