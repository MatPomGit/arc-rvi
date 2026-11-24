# Study 01: Reproducible Simulation Benchmark for Autonomous Robotic Visual Inspection

Protocol version: 1.4.1

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does scenario diversity expose a larger loss of task success than nominal testing?
For each method, compare nominal success with success in a balanced challenge suite.
The primary contrast is the difference in these losses between two frozen methods.
Select the reference method on development data before the confirmation split is opened.

Proposed hypothesis: Challenge conditions cause different success degradation across the two frozen methods.

## Design and baselines
Use a nominal condition and a crossed challenge design within geometry families.
For the current pilot, cross occlusion and clutter at reference brightness as
specified in the ICAISC amendment below. Illumination is a conditional future
factor, not an eligible primary factor without the specified validation.
Define measurable levels in the simulator configuration.
Use equal condition weights, independent scene draws and paired scenario seeds across methods.
Reserve complete geometry families for confirmation; repeated seeds from one geometry
remain in the same partition.

Compare a fixed shot list, greedy coverage with a separate route, and the existing
distance-penalized greedy baseline. Give each method the same candidate generator,
observations, motion constraints and mission budget. For the planning-only benchmark,
supply the correct target to every method and label identity assignment as controlled.
Do not infer localization performance from these runs. Record any oracle information.
An undocumented random sampler is not an acceptable experimental baseline.

## Endpoint and failure
Define task success as correct target assignment, required valid coverage achieved,
no collision or interlock violation, and completion within the frozen budget.
Freeze the coverage threshold, quality tests and budget after the pilot.
Success degradation is nominal success proportion minus challenge success proportion,
in percentage points. Negative values are possible and must be retained.
Also report each condition separately, route length, runtime and failure category.

## Unit, analysis and acceptance
The independent sampling and inference unit is the generated geometry family.
Scene instances are nested within families; condition cells and paired seeds are
within-family computational replicates, not independent families or physical objects.
Weight independent families equally in the primary contrast.
Estimate the paired difference in degradation with a family-clustered interval.
Method-by-condition interactions and ranking changes are secondary analyses.
If too few families support cluster inference, report descriptive estimates only.

Before confirmation, implement scenario generation, simulator ground truth and all
baselines; verify collision and coverage calculations on known geometries.
A fixture suite can check the analysis pipeline but cannot establish simulator robustness.

## Exploratory scenario-family generator

The [sampled-geometry implementation](../../docs/population.md) can draw
independent synthetic latent family parameters and preserve disjoint family splits.
Its sample space is prescribed by an uncalibrated 2D model. Its 12 pilot families
are **computational draws**, not real-world independent objects and not a
pre-registered confirmatory sample. The separate [12-cell exploratory factor
matrix](../../docs/population.md) now crosses model occlusion, illumination
proxy and nuisance discs over stratified 2–4-patch families. It has not been
calibrated, estimated with a factorial analysis or locked for confirmation.
The [pre-confirmatory sensitivity calculator](../../docs/sample-size.md)
provides illustrative normal-model estimates of independent family counts,
conditioning on externally specified effects, between-family SD and attrition.
The locked confirmation design and its validated power analysis remain pending.

## Exploratory observation-only view selection

The [sensor-aware smoke benchmark](../../docs/benchmark.md) now ranks candidate
views using public poses and past anonymous pixel/range features only, and
scores coverage from actually detected surfaces in an evaluator-only channel.
Its three policies (route order, nearest pose, parallax from prior detections)
are **engineering comparators**, not the prospectively defined and frozen
coverage-greedy primary baselines. A crossed **toy-model generation matrix** now
exists, but independent sensor validation, factorial effect estimation,
sample-size gate and sealed confirmatory split remain unimplemented.
Do not mix results of this mode with existing known-geometry oracle benchmarks.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 01](../../papers/paper01/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Literature-derived factorial candidate (unfrozen)

The [literature intake](../../docs/literature.md) suggests a candidate grid of
100/500/1000/2000 lux, ±10 cm object translation, ±15° rotation and
0/25/50/75% externally measured occlusion. **These are proposals, not
validated simulator settings or achieved physical conditions.** Select
measurable condition levels and family/sample counts only after model
calibration and an independent-unit power sensitivity study. Preserve the
current primary paired degradation contrast; do not replace it with a
post-hoc omnibus significance test.

## ICAISC 2027 pilot design amendment (prospective, 2026-11-24)

Publication decision: simulation-only P01; see the existing manuscript README.
This amendment specifies development and pilot requirements, not a frozen design.
No physical validity or confirmation is implied.

### Information parity and factor eligibility

Use a primary known-geometry planning track if coverage-greedy cannot be
implemented with the same observation-only information as all other policies.
In that track all policies may access the same declared model geometry and
predicted visibility; the independent evaluator scores executed acquisitions.
Alternatively, use an observation-only track with a common observable state and
implement all comparators against that state. Do not combine tracks or use oracle
coverage to select actions in the observation-only track. Choose one primary
track before confirmation. The other may be exploratory and separately labelled.

The candidate fuzzy planner is developmental. Its inputs may include predicted
marginal coverage, travel cost and a defined uncertainty proxy available to all
policies in the selected track. Normalize inputs using development-only bounds;
freeze membership functions, rules, defuzzification, tie-breaking and fallback
before evaluation. Include a fixed-weight score ablation with the same inputs
and feasible candidate set. No claim of novelty or benefit is made yet.

Use the existing factor registry. The nominal cell is no occluder, reference
brightness and no nuisance obstacle. Pilot occlusion and clutter with the existing
modelled geometry. Brightness is currently a dimensionless proxy that does not
change detection probability. Exclude illumination from the primary challenge
contrast unless its observation mechanism passes independent synthetic reference
checks before lock. Do not report lux or physical illumination robustness.
This amendment supersedes earlier illumination-factor proposals for the current
pilot. When excluding brightness, use only its reference level: the remaining 3 by 2
occlusion/clutter grid has one nominal and five equally weighted challenge cells.
Geometry strata remain balanced; record any unsupported cells before seeing outcomes.

### Paired estimand and scoring

For family f, method m and eligible cell c, let S(f,m,c) be mean binary mission
success over the fixed paired scene replicates. Define L(f,m) as S(f,m,nominal)
minus the equal-weight mean S(f,m,c) across challenge cells. The primary contrast
is mean across independent families of L(f,reference) minus L(f,candidate).
Positive values indicate smaller degradation for the candidate, not necessarily
better absolute performance. Report nominal and challenge success separately to
expose floor effects. Use percentage points
for reporting. Pair scenarios across policies and retain all initiated eligible
attempts. An algorithm failure, timeout, collision or inadequate valid coverage
scores zero; infrastructure failures remain explicitly missing, with linked
replacements and worst/best-case sensitivity bounds. Before confirmation, freeze
an outcome- and method-independent adjudication rule based on infrastructure logs.
Use a predeclared replacement seed schedule: repeat the complete paired method
block for the affected family/cell, preserve original attempts and replacement
links, and never replace an algorithm failure. Freeze retry limits and the
analysis rule for choosing original or replacement blocks before outcomes.
Compute sensitivity bounds by assigning unresolved binary outcomes zero or one
in the direction that minimizes or maximizes the paired contrast, retaining the
fixed cell and family weights. No missing cell may be silently dropped or reweighted. Report family counts and uncertainty at family
level; replicates and cells are not independent families.

### Pilot exit and confirmation lock

- [ ] Verify the common candidate set, information contract, motion budget,
  independent evaluator, coverage threshold and success rule with analytic fixtures.
- [ ] Verify supported factor manipulations, deterministic pairing and all failure
  categories; decide and document the primary information track.
- [ ] Run development/pilot only, record complete cell denominators and hashes,
  and assess family variability, floor/ceiling effects and runtime.
- [ ] Justify smallest relevant difference and family count using sensitivity
  analysis and small-sample Monte Carlo coverage; freeze the primary comparator,
  contrast, multiplicity policy, stopping rule and missing-data treatment.
- [ ] Freeze source/configuration hashes, new disjoint confirmation families,
  seeds and analysis code before accessing outcomes. Record exact component
  revisions, immutable hashes and explicit researcher sign-off (pending until
  actually granted) in the protocol lock record required by issue #38.
  The existing public holdout is not a sealed confirmation set.

Confirmation remains BLOCKED until these gates and the project-wide freeze gate
are satisfied. If the deadline prevents defensible confirmation, report only
explicitly exploratory simulation evidence or record NO-GO.
