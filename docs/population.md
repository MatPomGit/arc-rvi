# Exploratory sampled geometry families (Study 01)

This is a **software-generated scenario population**, not a sample of physical objects and not a confirmatory dataset. It extends the fixed six-family regression generator without replacing its historical fixtures.

## Reproduce

From an editable local package installation (Python 3.11 or later):

```bash
rvi population --spec simulation/conditions/study01_population_pilot.json --output-dir results/study01_population
rvi pilot --manifest results/study01_population/manifest.json --output results/study01_population_analysis.json
```

Both commands fail if an output target already exists. The `pilot` command processes only the pilot partition and deliberately does not open the holdout scene files. The public holdout suite is nevertheless **not blinded confirmation**: the generator, seeds, distribution and output path are visible.

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

There are no illumination or clutter sensor factors, unknown-surface perception measurements, physics-engine calibration, real-world reference samples, realistic robot dynamics, frozen success thresholds or verified power calculations. A confirmatory study requires a *separate* predeclared sampling frame with independently justified scenario difficulty and sample size, protocol lock before examination of confirmatory outcomes, and independent validation of simulated assumptions.

Related: [prospective Study 01 protocol](../experiments/exp01_benchmark/protocol.md), [pilot statistical estimand](pilot-analysis.md), [simulation limits](simulation.md).
