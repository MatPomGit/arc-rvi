# Exploratory paired analysis for study 01

This command processes **only** the pilot partition of the seeded planar-geometry
generator. It does not access holdout outcomes or perform physical validation.
It reevaluates the original paired scenes and checks SHA-256 hashes for the
manifest, suites, scenes and trial provenance before summarizing outcomes.

## Reproduction

Run after installing the package from this source checkout:

    rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/study01_conditions
    rvi pilot --manifest results/study01_conditions/manifest.json --output results/study01_pilot_analysis.json

Both commands refuse to overwrite existing outputs. The analysis defaults to
fixed_order as the reference and greedy_distance as the comparator. These are
**software-pilot defaults only**: the confirmatory reference method remains
unselected. To examine an alternative exploratory contrast, supply
--reference and --comparator with distinct registered method IDs. The default
bootstrap seed is 20261026; the reproducible result includes the seed.

## Outcomes and estimand

A completion means **all reference surface patches acquired in the planar
model**, not operational inspection success. Reference geometry is visible to
the evaluated policies. Coverage is area-weighted sampled reference coverage.
Algorithm failures remain in every denominator, with failure counts reported
by method and condition.

For each paired geometry replicate and method, let L denote the nominal
completion or coverage fraction minus the occluded fraction. The displayed
effect is L(comparator) - L(reference). Positive values mean **larger
occlusion-associated loss** for the comparator. Effects are first averaged
within each geometry family, then averaged equally across families.
Replicate seeds and individual acquisitions are not independent families.

The current pilot has **two geometry families, six pairs and 36 method trials**.
It reports descriptive contrasts without confidence intervals or significance
tests. Code for a deterministic 10,000-resample percentile bootstrap exists
for future exploratory datasets with at least eight independent families; this
threshold is a conservative software guard, **not** a sample-size calculation
or a guarantee of correct population coverage. Cluster resampling is at the
family level and retains paired method/condition comparisons.

## Research gates

- Do not claim lighting, clutter, unknown geometry, sensor accuracy, robot
  performance, hypothesis confirmation or publication results from this model.
- Do not tune methods or thresholds on holdout data. The public deterministic
  holdout is not a blinded confirmatory dataset.
- Before any confirmation, independently define the sampling population,
  frozen primary contrast, success thresholds, sufficient cluster count,
  calibration and full crossed challenge factors.
- Retain raw benchmark reports externally if needed for later audit. The
  summary records a hash of the transient benchmark report and its source
  provenance; that hash does not by itself archive the report.

See experiments/exp01_benchmark/protocol.md and
experiments/analysis/README.md for the prospective scientific plan.
