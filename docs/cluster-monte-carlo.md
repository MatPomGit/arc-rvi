# Exploratory cluster Monte Carlo: P01

**Status:** Simulation-only numerical method check; not a preregistered confirmatory design. The command models independently drawn **paired family-level contrasts**, not physical objects or robot sessions.

## Reproduction

```bash
rvi power-mc --spec simulation/conditions/study01_cluster_mc.json --output results/study01_cluster_mc.json
```

The versioned JSON contains the master seed, Monte Carlo repetitions, the number of *nested computational replicates per family*, a two-sided confidence level, a synthetic alternative effect, and each sensitivity scenario. This is a **generative mathematical stress model**, not measured variability.

## Simulated generative model

For family `i` and nested replicate `j`, the simulated contrast is:

```text
D_ij = delta + family_effect_i + nested_noise_ij
family_effect_i = sigma_between * Z_i
nested_noise_ij ~ Normal(0, sigma_within^2)
```

The independent unit is the family mean of its nested contrasts. The distribution of `Z_i` is either standard Normal or variance-standardized Student-t with five degrees of freedom. Missing-family draws may be independent or intentionally associated with the sign of the latent family effect. Such outcome-dependent missingness is a **bias stress case**. Individual nested replicates never become independent degrees of freedom.

Each scenario is run both with `delta = 0` and with the specified alternative `delta`. Per-run intervals use the sample SD of **observed family means**, either a normal z critical value or an *approximate* Student-t critical value. A Student-t quantile expansion is used because this lightweight dependency-free tool is not an exact t-distribution implementation. This is disclosed in every result.

## Outputs and interpretation

The report includes each cell's observed family count, estimable vs non-estimable repetitions, empirical interval coverage, null-rejection fraction, alternative-rejection fraction, estimation bias, interval width and Monte Carlo standard errors. For the null cells, empirical rejection is an estimate of type-I error; for alternative cells, an estimate of power *conditional on the synthetic model*. The bootstrap, permutation, heteroskedastic model, and crossed object/operator/session components are **not** implemented here.

The checked-in example covers 8/16/40 nominal independent families, lower/higher between-family variability, normally distributed and heavy-tailed family effects and independent/outcome-linked missingness. Simulation repetitions and total sampled observations are capped to keep offline work bounded.

**Do not** choose a confirmatory sample size on these results alone. The model does not establish the target population, minimal relevant effect, calibrated variation, real-world quality, physical robot behavior, or nonrandom field missingness. Decisions still require [protocol gating](../experiments/exp01_benchmark/protocol.md) and the [shared statistics plan](../experiments/analysis/README.md).

Further work: [Issue #19](https://github.com/MatPomGit/arc-rvi/issues/19).
