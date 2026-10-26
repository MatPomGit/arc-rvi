# Shared statistical analysis plan

Version: 1.1.0

Status: prospective specification; analysis software is not implemented

## Estimands and denominators

Each protocol specifies one primary endpoint and one primary contrast.
Fix the direction of benefit, reference method and aggregation weights before confirmation.
Report absolute paired differences with 95% confidence intervals and all denominators.
Do not pool fixture, simulation and physical observations into one effect estimate.

For area-weighted coverage, let the target surface have reference triangles with areas
`a_j`. Coverage is `sum(a_j * valid_j) / sum(a_j)`, where `valid_j` is one only when
at least one acquired image meets all frozen visibility and quality requirements.
Specify range, incidence, occlusion, resolution and reference-registration tolerances.
Use a fixed inspectable surface mask chosen before method outputs are available.
Report the excluded surface fraction. Do not redefine the denominator after a failure.
Study 08 instead uses the proportion of an equally weighted required-region shot list.

## Sampling and partitions

Define the population to which inference applies. Distinguish independent scene or
session draws from repeated views, requests, seeds and simulator reruns.
Keep object instances and sessions grouped across development and confirmation splits.
When testing geometry transfer, hold out full geometry families as well.
Store split assignments and hashes before evaluation. Share paired scenarios across
methods without leaking evaluator ground truth to a method.

Randomize method order within physical blocks and balance period effects.
Use separate random streams for scene generation, sensor noise and method randomness.
Adaptive methods may consume different numbers of observations; index environmental
noise by simulated time or event identity rather than by sequential random draws.
Record any coupling that cannot be preserved.

## Pilot and sample size

Use pilot data only for feasibility, variance, thresholds and sample-size planning.
Exclude pilot observations from confirmation estimates.
Before confirmation, choose a scientifically meaningful effect or precision target.
Simulate or calculate the required independent cluster count using pilot variance,
within-cluster dependence, expected failure and planned paired analysis.
For study 08, use the justified non-inferiority margin rather than a superiority effect.
Record assumptions, calculation code and sensitivity to variance and dropout.
No universal trial count is prescribed while these quantities remain unknown.

Stop at the frozen independent-unit count. Predefine permitted replacements for
external measurement failures. Do not stop because an observed result looks favourable.

## Estimation and inference

Prefer paired block-level estimates. For a clustered bootstrap, resample independent
clusters with replacement and retain all paired methods and nested observations.
Use 10,000 replicates and a recorded analysis seed; report the interval construction.
For crossed object/session/operator sampling, freeze a suitable crossed-effects model
or multiway resampling scheme before confirmation. A one-level bootstrap is insufficient.
If the number of independent clusters is inadequate, limit inference to descriptive
results and collect further independent units under a documented protocol amendment.

A confirmatory test is two-sided at 0.05 unless a protocol explicitly specifies another
rule. Study 08 uses its stated interval rule for non-inferiority.
One frozen primary contrast per paper defines its primary inferential family.
Apply Holm adjustment to any additional confirmatory comparisons within that paper.
Label ablations, subgroup analyses and additional endpoints exploratory unless explicitly
frozen otherwise. Report all planned comparisons, including negative findings.

## Failures, missingness and deviations

Retain every initiated eligible trial with method, condition, outcome and reason code.
Distinguish algorithm failure, deadline, safety abort, missing sensor measurement and
external infrastructure failure. Record timeouts as outcomes, not missing rows.
Apply each protocol's scoring rule to partial coverage, absent poses and capped time.
Never replace undefined pose error with zero or discard failed runs silently.

Freeze eligibility and exclusion rules before collection. For an external failure,
keep the original record and link any replacement trial. Report counts by method and
condition. Describe missingness, plausible bias and a predeclared sensitivity analysis.
Record deviations with date, reason and whether outcomes had been inspected.

## Reporting package

Provide a trial-flow table, independent-unit counts, per-method outcomes, the primary
contrast with uncertainty, secondary costs and a failure table.
Regenerate every table and figure from versioned inputs using a single documented
analysis command once that implementation exists. Keep evaluation code independent
of method-specific acceptance flags. Check results against hand-calculable fixtures
before using the pipeline on experimental evidence.
