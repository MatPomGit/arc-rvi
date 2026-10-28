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

## Exploratory sensor proxy

An [initial generated-observation check](../../docs/localization.md) now
compares anonymous horizontal-bearing and range features using the
unchanged selection/abstention mechanism. It includes present/absent
target requests and independently held evaluator correspondence. These
proxies are **not** appearance embeddings or full spatial-visual fusion;
the protocol's main hypothesis remains untested.

Manuscript: [paper 02](../../papers/paper02/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Grouped exploratory factor pilot

The [P02 family generator](../../docs/localization.md) now provides disjoint
synthetic family partitions and a crossed near/far separation × clear/blocked
visibility design with paired present/absent identity requests. The evaluator
holds the geometry-to-detection identity mapping until after prediction.
A family, rather than a repeated sensor capture, is the unit for descriptive
method contrasts. This is neither image-feature fusion nor a calibrated
object identity population; the prospective hypothesis and thresholds remain
unfrozen. Study-specific independent session sampling and visual similarity
conditions are still required before confirmation.


## Synthetic pixel-array association extension

A [new grayscale pilot](../../docs/localization.md) supplies 8×8
simulated crops for anonymous detections, with exactly controlled
target/distractor pixel similarity. The comparison has three methods:
normalized grayscale MAE, range-only proxy and equal-weight grayscale/range.
The synthetic session offset induces within-session dependence; repetitions
are not treated as independently sampled objects or physical sessions.
All methods see the same requests, including absent-target hard negatives.
Only family-aggregated descriptive contrasts are permitted. A successful
software test does not establish natural-image accuracy, calibration or
the protocol's visual-spatial fusion hypothesis.


## Operator-supplied image replay (offline)

The [versioned PGM dataset interface](../../docs/localization.md) can
consume separately recorded anonymous image crops and independent
evaluator annotations, with strict source hashes, UTC-aware timestamps,
object-family/session metadata and a sealed exploratory holdout mode.
The evaluation reuses exactly three simple baselines: image MAE, declared
range difference and equal-weight fusion. Missing frames and absent
targets remain in the denominator; groups must be genuinely independent
for scientific interpretation.

The interface cannot confirm that supplied images came from a calibrated
sensor, that annotations were independently measured or that cropped
appearances generalize to new objects. Operator declarations do not replace
calibration records, a verified sampling population, data-rights review or
prospective confirmation. Thresholds remain exploratory.

## New prior-art comparator boundary (2026-10-27)

[Fusion++ (McCormac et al., 2018)](https://doi.org/10.1109/3DV.2018.00015)
provides object-level RGB-D SLAM with instance tracking, and
[RoboEye (Zhang et al., 2025, preprint)](https://arxiv.org/abs/2509.14966)
combines 2D appearance with selective geometric reasoning for ambiguous
warehouse object identification. Thus visual/spatial fusion and object
re-identification are already researched. P02 must validate the
**different inspection-specific error/abstention tradeoff** against
held-out object/session identity truth and calibrated poses. The current
8×8 simulated textures and uncalibrated PGM input do not meet that gate.
See [prior-art appraisal](../../docs/prior-art-critical.md).

## Primary vehicle-instruction grounding task (prospective, 2026-10-28)

The project reference scenario is a person commanding the bipedal robot
to photograph **a particular car**, or only its **front/rear bumper**,
before returning. See the [mission contract](../../docs/vehicle-inspection-missions.md).
P02 now explicitly includes a two-stage decision: (i) referential grounding
of the intended *vehicle instance* among several parked or visually similar
cars and (ii) part-to-parent matching for an instructed component.
"Front" and "rear" refer to the vehicle's intrinsic coordinate frame,
not to the robot's current heading.

Prospective matched strata: one unambiguous vehicle, two near-identical
vehicles, target absent, occluded/partially visible target, part absent,
left/right spatial language, human pointing or spoken clarification.
Keep independent car-family, parking-layout and recording-session splits.
A model's confidence alone does **not** authorize selecting an ambiguous
vehicle; compare confidence calibration, explicit abstention and
clarification. Score wrong-car selection as a failure even if later images
have adequate sharpness. Wrong-part, wrong-parent and misunderstood
front/rear requests are separate errors. The two-stage system must be
compared against visual-only, spatial-only and human-clarification variants.

[LEGS-POMDP (HRI 2026)](https://arxiv.org/abs/2603.04705) and
[LINGO-Space (AAAI 2024)](https://doi.org/10.1609/aaai.v38i9.28898)
establish ambiguity-aware language grounding prior art. A new P02 claim
requires independent *vehicle/part* evidence, not "first language-guided
robot search". The current grayscale 8x8 proxy cannot evaluate this task.
