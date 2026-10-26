# Study 02: Robust Instance-Level Object Localization in Multi-Object Environments for Humanoid Robots

Protocol version: 1.1.0

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does spatial-visual fusion reduce wrong-instance selection compared with a frozen
unimodal reference? Choose the reference using development data only.
Compare methods on the same target requests and sensor observations.

Proposed hypothesis: Fusion reduces wrong-instance selection while satisfying the frozen correct-selection requirement.

## Design and baselines
Cross distractor similarity, occlusion and target separation. Include absent-target
trials and scenes with several near-identical instances. Assign ground-truth identities
independently of the identifiers exposed to the algorithm.
Compare visual matching, geometry-only association and fused association.
A synthetic marker baseline provides a controlled reference when markers are observable.
Ablate spatial association and temporal accumulation separately.

Hold out complete object instances and acquisition sessions. Fit appearance models,
confidence thresholds and calibration on development objects only.
Physical confirmation requires an independently measured reference pose and a
calibration uncertainty smaller than the localization tolerance.

## Endpoint and failure
The primary endpoint is wrong-instance selection count divided by all eligible target
requests, including abstentions and absent-target requests. Correct rejection is not a
wrong selection. Report abstention and correct-selection proportions alongside it,
so a method that always abstains cannot be interpreted as successful localization.
Freeze a minimum correct-selection requirement before confirmation.

Secondary endpoints are translation error in metres and orientation error in degrees
for correct assignments, plus deadline compliance. Report conditional pose error with
its assignment denominator; never assign zero pose error to an abstention.
An incorrect identity remains a failure even when the estimated position is nearby.

## Unit, analysis and acceptance
The independent unit is an object-set/session block. Requests and video frames are
nested observations. Estimate paired wrong-selection risk differences with intervals
clustered at the independent block; report absent/present strata separately.
Freeze pose tolerances, deadlines and the abstention policy after the pilot.
Before confirmation, verify identity scoring, coordinate transforms, timestamp alignment
and independent ground truth. Synthetic localization alone supports simulation claims.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 02](../../papers/paper02/manuscript.tex).
Publication boundaries: [research program](../README.md).
