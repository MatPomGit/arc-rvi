# Study 04: Uncertainty-Aware Active Visual Coverage of Partially Unknown Objects

Protocol version: 1.1.2

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

## Contact-limited unknown-terrain access (unfrozen)

P04 studies inspection of **partially unknown target surfaces**,
not locomotion policy optimization. Distinguish uncertainty in the
target geometry from uncertainty in the **support terrain**:
withheld reference terrain/target geometry may be used for scoring
but never for selecting the next view. A foothold or retreat path
unsupported by available onboard observations is not a valid
executed viewpoint. Compare NBV policies only over shared,
physically feasible stances or record rejected attempts and consumed
time using the same contact-risk oracle. Premature stopping because
only safe positions remain must count as a budget-capped failure
when the true coverage threshold is unmet.

Use scenario-family groups spanning occluded near-floor targets,
slopes/steps, narrow clutter and camera-head motion, conditional on
independent simulator validity. Report terrain-induced **unreachable
area** and estimated uncertainty separately from image-quality
failure; retain unknown or unsafe regions in the required-surface
denominator unless the experimental task definition prospectively
excludes them for *all* methods. No locomotion source alone
establishes success for this inspection endpoint.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 04](../../papers/paper04/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Updated comparator requirement (2026-10-28)

A second independently identified source, [Staderini's 2026 doctoral
thesis](https://repositum.tuwien.at/handle/20.500.12708/226537),
integrates surface sampling, photometric visibility and inspection-route
optimisation. Its model assumes CAD-derived mesh geometry and therefore
is **not** directly equivalent to the unknown-surface online P04 task.
When using it as a reference, distinguish **geometry-known offline
planning** from **policy-observation-only active coverage** and disclose
the differing information available to each method.

[Bettles et al. (arXiv, 2026)](https://arxiv.org/abs/2603.16471)
already describe physical NBV coverage with online geometric estimation
and chance-constrained obstacle avoidance. Their abstract alone supplies
no independently checked physical surface-denominator definition,
trial count or uncertainty interval. A P04 comparison needs withheld
reference geometry, a documented physical/simulated measurement model,
paired scene families and time-capped failures; do not quote abstract-level
coverage as a numerically validated matched baseline.

These requirements refine **comparability**, not the previously stated
primary contrast or a claim of successful ARC-RVI experiments.

## Reported physical NBV prior art

[Bettles et al. (2026, arXiv)](https://arxiv.org/abs/2603.16471) report
physical mobile-manipulator pipe-network inspection, online geometry and
stochastic obstacle constraints. The source is a **preprint**, and its
reported physical experiments have not been replicated by ARC-RVI. P04 must
therefore avoid a broad novelty claim for physical NBV coverage; it should
compare a prespecified unknown-surface, observation-only policy on matched
budgets and separated hidden evaluator geometry. Do not double-count P03
planning outcomes as independent P04 evidence.
