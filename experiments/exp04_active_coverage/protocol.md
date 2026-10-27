# Study 04: Uncertainty-Aware Active Visual Coverage of Partially Unknown Objects

Protocol version: 1.1.0

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does uncertainty-guided next-view selection reach a fixed coverage target at lower
acquisition cost than a frozen next-best-view reference?
Both methods start with the same partial observation and sensor budget.

Proposed hypothesis: Uncertainty-guided selection reduces budget-capped acquisition time at the frozen coverage threshold.

## Design and baselines
Use held-out shape families, controlled initial visible fractions and several
occluder arrangements. Keep the true surface available only to the evaluator.
Compare a static path, nearest unseen estimated surface, a specified geometric
next-best-view method and uncertainty-guided selection.
Freeze the reference acquisition function and its implementation before confirmation.
Ablate uncertainty weighting and online surface updates independently.
Keep uncertainty calibration data separate from evaluation shapes and sessions.

## Endpoint and failure
The primary endpoint is budget-capped time to first reach the true valid-coverage
threshold. Use elapsed acquisition and movement time, not a freely weighted cost.
For runs that never reach the target, assign the full time budget and record failure.
This capped measure is a resource endpoint; it is not uncensored completion time.
Report success probability, accepted view count and travelled distance separately.

Freeze threshold and budget after pilot sensitivity analysis. Compute true coverage
from reference geometry. Log estimated online coverage separately to quantify premature
stopping. Reaching an estimated threshold without reaching the true threshold is failure.
Report uncertainty calibration against a defined surface-error event on held-out data.

## Unit, analysis and acceptance
The independent unit is a shape/occlusion instance, clustered by shape family.
Pair initial observations and noise streams across methods where causally compatible.
Estimate paired capped-time differences with clustered intervals; give success and
final coverage to interpret budget-capped failures.
Before confirmation, check that hidden geometry cannot enter the planner, define
physical reference-scan registration uncertainty, and validate stopping logic.
Do not equate a heuristic score with epistemic uncertainty without a defined model.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 04](../../papers/paper04/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Reported physical NBV prior art

[Bettles et al. (2026, arXiv)](https://arxiv.org/abs/2603.16471) report
physical mobile-manipulator pipe-network inspection, online geometry and
stochastic obstacle constraints. The source is a **preprint**, and its
reported physical experiments have not been replicated by ARC-RVI. P04 must
therefore avoid a broad novelty claim for physical NBV coverage; it should
compare a prespecified unknown-surface, observation-only policy on matched
budgets and separated hidden evaluator geometry. Do not double-count P03
planning outcomes as independent P04 evidence.
