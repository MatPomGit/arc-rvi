# P01 independent-family precision and power sensitivity

Status: **illustrative design sensitivity; not a frozen or preregistered protocol**.
The `precision` command is an offline Python standard-library utility. It plans
numbers of *independent geometry families*, not numbers of images, capture events,
paired conditions or repeated computational seeds.

## Reproduce

```bash
rvi precision --spec simulation/conditions/study01_precision_sensitivity.json --output results/study01_precision.json
```

Optionally inspect an exploratory pilot summary without using its estimated
variance to set the sample size:

```bash
rvi precision --spec simulation/conditions/study01_precision_sensitivity.json --pilot-summary results/study01_population_analysis.json --output results/study01_precision_with_diagnostics.json
```

The `--pilot-summary` input is produced by `rvi pilot` and must contain
known-geometry exploratory *pilot* effects aggregated by family. The output
records its SHA-256 and observed family-level SD as a **diagnostic only**.
The choice of assumptions remains fully explicit in the JSON spec. Existing
output files are not overwritten.

## Estimand and assumptions

The planning estimand is the difference between comparator and reference
methods in their nominal-minus-occluded completion losses (fractional scale).
The method-specific completion endpoint is defined by the planar oracle model.
An effect of 0.15 means an **absolute 15-percentage-point difference**, not a
relative 15% change. A between-family SD refers to the *already averaged,
paired family contrast*. Repeated scenes within a family do **not** increase n.

The example uses a two-sided confidence level of 95%, target power of 80%,
minimum 8 complete families, an illustrative effect of 0.15 and an illustrative
confidence-interval half-width target of 0.10. None of these values has been
established as a minimum scientifically relevant effect or measurement
uncertainty in real inspections.

For complete independent families, the **known-variance normal/Wald
approximation** uses:

- Precision: `n_ci = ceil((z_(1-alpha/2) * sigma / h)^2)`.
- Two-sided power: `n_power = ceil(((z_(1-alpha/2) + z_power) * sigma / delta)^2)`,
  with a final direct normal-power check.
- `n_complete = max(minimum_families, n_ci, n_power)`.
- Enrollment sensitivity: `n_enrolled = ceil(n_complete / (1 - unusable_fraction))`.

Each input scenario must provide its own SD and expected unusable-family
fraction. Neither formula accounts for small-sample Student-t quantiles,
non-normal distributions, uncertainty in the estimated SD, crossed effects,
nonrandom attrition or multiple confirmatory endpoints. Enrollment inflation
protects only the **expected** number of complete families; it does not
guarantee that number. The resulting power is conditional on the assumed SD,
effect size and normal model.

## Example scenario sensitivity

These numbers are **illustrative calculations**, not recommended recruitment
targets and not observations from a completed experiment.

| Assumed SD of family contrast | Unusable families | Complete families | Enrolled families |
| ---: | ---: | ---: | ---: |
| 0.12 | 5% | 8 | 9 |
| 0.20 | 10% | 16 | 18 |
| 0.32 | 20% | 40 | 50 |

Increasing the variability or assumed unusable-family fraction can
substantially increase the required number of independent draws. In particular,
the 12 synthetic *pilot* families from the separate population generator are
not an empirical basis for committing to one of these rows.

## What must precede protocol lock

Before any confirmation, the study needs a justified sampling frame for the
target inference domain, a meaningful primary effect, frozen completion and
failure rules, independently calibrated model assumptions, independent
between-family variability estimates, and a robust small-sample or simulation-
based power assessment. The complete crossed geometry × occlusion ×
illumination × clutter design remains unavailable. No use of public synthetic
holdout data is allowed to determine primary choices.

This planner is **not** a substitute for preregistration, external calibration,
real-object representativeness or a permission to execute physical experiments.
See [study 01 protocol](../experiments/exp01_benchmark/protocol.md),
[shared analysis plan](../experiments/analysis/README.md) and
[sampled model limitations](population.md).
