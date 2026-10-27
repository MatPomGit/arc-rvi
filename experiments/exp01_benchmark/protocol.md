# Study 01: Reproducible Simulation Benchmark for Autonomous Robotic Visual Inspection

Protocol version: 1.3.0

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does scenario diversity expose a larger loss of task success than nominal testing?
For each method, compare nominal success with success in a balanced challenge suite.
The primary contrast is the difference in these losses between two frozen methods.
Select the reference method on development data before the confirmation split is opened.

Proposed hypothesis: Challenge conditions cause different success degradation across the two frozen methods.

## Design and baselines
Use a nominal condition and a crossed challenge design: geometry family, occlusion,
illumination and clutter. Define measurable levels in the simulator configuration,
including visible surface fraction, light intensity and obstacle density.
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
The independent unit is a generated scene instance, grouped by geometry family.
Seeds are paired computational replicates, not independent physical objects.
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
pre-registered confirmatory sample. Illumination and clutter are not modeled.
The [pre-confirmatory sensitivity calculator](../../docs/sample-size.md)
provides illustrative normal-model estimates of independent family counts,
conditioning on externally specified effects, between-family SD and attrition.
The locked confirmation design and its validated power analysis remain pending.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 01](../../papers/paper01/manuscript.tex).
Publication boundaries: [research program](../README.md).
