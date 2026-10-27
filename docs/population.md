# Exploratory sampled geometry families (Study 01)

This is a **software-generated scenario population**, not a sample of physical objects and not a confirmatory dataset. It extends the fixed six-family regression generator without replacing its historical fixtures.

## Reproduce

From an editable local package installation (Python 3.11 or later):

```bash
rvi population --spec simulation/conditions/study01_population_pilot.json --output-dir results/study01_population
rvi pilot --manifest results/study01_population/manifest.json --output results/study01_population_analysis.json
```

Both commands fail if an output target already exists. The `pilot` command processes only the pilot partition and deliberately does not open the holdout scene files. The public holdout suite is nevertheless **not blinded confirmation**: the generator, seeds, distribution and output path are visible.

## Crossed exploratory factor matrix (P01)

```bash
rvi population --spec simulation/conditions/study01_factorial_pilot.json --output-dir results/study01_factorial
rvi benchmark --suite results/study01_factorial/suites/pilot/o_moderate__i_low__c_dense.json --sensor results/study01_factorial/sensors/low.json --output results/factorial_cell_report.json
```

The existing `population` command now also recognizes `sampled_factorial_v1`,
without changing the earlier `sampled_geometry_v1` outputs. The example creates
18 disjoint, **artificial** geometry families (six per split), one replicate per
family and all **12 cells per replicate**, yielding 216 model scenes.
Within every split, family counts are balanced between 2, 3 and 4 patch
geometry strata; each cell therefore has six scenes. A distinct SHA-256
manifest lists family, stratum, paired geometry seed, cell factors, scene
content hash, suite hash and illumination-specific sensor configuration.

| Manipulation | Declared levels | Implemented toy representation |
| --- | --- | --- |
| Geometry | 2, 3, 4 patches | Independently drawn 2D patch layouts, stratified by family |
| Occlusion | none, moderate, strong | First-patch line-of-sight disc radius 0, 0.12, 0.32 m |
| Illumination | low, reference | Synthetic light multiplier 0.35, 1.0 (dimensionless) |
| Clutter | none, dense | Zero or two nuisance obstacle discs of radius 0.12 m |

Every cell of a family/replicate shares **identical patch geometry, route and
motion budget**; only declared factors change. The sensor and geometry seeds
use separate SHA-256 namespaces; sensor draws are paired between policies
within one exact scene, **not yet common across distinct factor-cell IDs**.
The illumination multiplier changes the brightness proxy but does **not**
alter current detection probability or optical contrast, and the three P01
smoke policies do not currently use brightness for decisions. Therefore this
factor is manipulated but **not yet a calibrated illumination stress test**.
Occlusion operates on representative points rather than pixel area; clutter
is additional planar obstacle geometry, not visual texture.

Sensor-based P01 comparison uses the per-cell `suites/<split>/<cell>.json`
and corresponding `sensors/<illumination>.json`. This is **one cell per run**,
not an automated factorial effect estimator. Existing `rvi pilot` and
`rvi batch` only accept the older nominal/occluded contract and must not be
used with the factorial manifest. The holdout files are generated and
inspectable, not blinded or preregistered; **do not treat them as
confirmatory evidence**. A separate frozen holdout release and cluster-level
factor analysis are still required.

## Sampling model

The checked-in example fixes seed `20261027`, 2 computational replicates per family and 2 paired conditions. It draws **32 latent families** from a fixed, explicitly limited planar distribution: 8 development, 12 pilot and 12 holdout. Every family is drawn using a separate SHA-256-derived stream. It fixes a family-level latent patch layout, then applies small, paired coordinate perturbations to the two replicate scenes. The nominal and occluded condition of each replicate have identical target geometry, camera poses and model parameters; only a single line-of-sight occluder differs.

The algorithm samples the patch count uniformly from 2–4. Patch x-coordinates are uniformly drawn from [2.6, 3.6] m; patch y-coordinates follow equal spacing over [-0.9, 0.9] m plus jitter in [-0.05, 0.05] m. Surface area is uniformly drawn from [0.75, 1.25] m². Replicate x/y perturbations lie in [-0.04, 0.04] m. The occluder radius is 0.28 m. Camera, motion and maximum-time settings are exactly those of the existing planar model and are not calibrated physical characteristics.

The number of sampled family identifiers is *not* a scientific power analysis. Families are independent **draws conditional on this artificial model**, not independent real-world objects. Replicate seeds within one family are nested observations, not additional independent sampling units.

## Design constraints and provenance

- Family identifiers are unique and disjoint across `development`, `pilot` and `holdout`. Full family-level split assignment precedes scene generation.
- SHA-256 identifies the exact input specification, generator source file, scene bytes and suite files.
- Same-family replicates share latent geometry; two conditions share every generated field except `scene_id` and `obstacles`.
- The `pilot` estimator is a family-equal-weighted paired difference of nominal-to-occluded losses, not a population claim.
- The analyzer computes exploratory family-resampled percentile intervals for 12 pilot families. These intervals describe **only the stipulated synthetic distribution** and cannot certify generalization or significance for field deployment.
- The original deterministic six-family generator and its smoke tests remain unchanged.

## What is still missing

Exploratory illumination and obstacle-clutter factors now exist, but there are still no calibrated sensor responses, unknown-surface perception measurements, physics-engine calibration, real-world reference samples, realistic robot dynamics, frozen success thresholds or verified power calculations. A confirmatory study requires a *separate* predeclared sampling frame with independently justified scenario difficulty and sample size, protocol lock before examination of confirmatory outcomes, and independent validation of simulated assumptions.

Related: [prospective Study 01 protocol](../experiments/exp01_benchmark/protocol.md), [pilot statistical estimand](pilot-analysis.md), [simulation limits](simulation.md).
