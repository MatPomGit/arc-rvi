# ARC-RVI research plan

Version: 1.1.0

ARC-RVI is a separate line in the ARC research portfolio. Its canonical status is
[PROJECT_STATE.yaml](PROJECT_STATE.yaml). The [eight-study index](experiments/README.md)
defines distinct scientific questions, publication boundaries and dependencies.
The controller maintains the portfolio index; scientific claims remain in this repository.

## Research sequence

| Package | Deliverable | Acceptance |
| --- | --- | --- |
| RVI-01 | Reproducible scenes and paired policy evaluation | Independent units, split manifest, hashes, preserved failures |
| RVI-02 | Target identity and coupled view/path planning | Independent ground truth, held-out geometry, feasible motion |
| RVI-03 | Adaptive coverage and quality-guided recovery | Estimated coverage separated from reference coverage; bounded retry cost |
| RVI-04 | Physical repeatability and transfer calibration | Independently measured pose/time and separate calibration sessions |
| RVI-05 | End-to-end documentation comparison | Frozen margin, assessment rules and applicable physical/participant procedures |
| RVI-06 | Publication readiness per study | Verified literature, distinct primary analysis and reproducible evidence |

The reference robot for planned simulation-model validation and authorized
physical tests is **Unitree G1 EDU** (`config/robot.yaml`). This selection
does not enable hardware control or assert ownership of a specific variant.
Retain vendor-neutral research algorithms and verify the particular robot,
sensors, SDK, kinematics, coordinate frames and safety model before deployment.

The software currently supports fixtures and planar geometric/kinematic simulation.
Candidate visibility comes from known geometry. Physics, physical acquisition and
unknown-geometry perception require separate implementations and validation.
The smoke suites check software arithmetic; they do not establish method superiority.

## Humanoid difficult-terrain work packages and agent handoff (2026-10-29)

The [master issue #6](https://github.com/MatPomGit/arc-rvi/issues/6)
contains the current **M0–M5 issue-based milestones** with independent
acceptance/evidence gates. It remains the source of truth for task order;
do not create parallel task queues, alternate roadmaps or new schedulers.

| Milestone | Atomic issues | Dependency and closing gate |
| --- | --- | --- |
| M0, model identity | [#98](https://github.com/MatPomGit/arc-rvi/issues/98) | Operator-approved **read-only** G1 EDU variant / URDF / sensor inventory, otherwise BLOCKED |
| M1, continuous proxy rotary collision | [#99](https://github.com/MatPomGit/arc-rvi/issues/99) → [#100](https://github.com/MatPomGit/arc-rvi/issues/100) | Independently verified conservative bound; no false all-clear in declared domain |
| M2, collision-volume coverage and IK | [#101](https://github.com/MatPomGit/arc-rvi/issues/101) → [#102](https://github.com/MatPomGit/arc-rvi/issues/102) | All relevant link volumes/constraints represented and independently cross-checked; unknown means unverified |
| M3, difficult-terrain contact and gait | [#103](https://github.com/MatPomGit/arc-rvi/issues/103) → [#104](https://github.com/MatPomGit/arc-rvi/issues/104) | Multi-level support/unknown traction plus time-indexed movement and aborts, **virtual only** |
| M4, terrain-aware inspect-and-return | [#105](https://github.com/MatPomGit/arc-rvi/issues/105) → [#106](https://github.com/MatPomGit/arc-rvi/issues/106); [#26](https://github.com/MatPomGit/arc-rvi/issues/26), [#88](https://github.com/MatPomGit/arc-rvi/issues/88) | Group-disjoint terrain, bounded independent view/route comparison, valid photos and return reserve |
| M5, physical readiness review | [#107](https://github.com/MatPomGit/arc-rvi/issues/107); [#18](https://github.com/MatPomGit/arc-rvi/issues/18), [#38](https://github.com/MatPomGit/arc-rvi/issues/38) | Site/robot/human signoff or explicit NO-GO; no robot actuation by the research runner |

**Historical virtual-first candidates (as of 2026-10-29):** #99 and #100.
Before starting new work, fetch live issue and PR state and select the first
unblocked stage; this prose is not an active task queue. M0 #98 may proceed
in parallel *only* with authorized read-only device access. All P03 geometry/contact work remains independent
of actual G1 EDU configuration until its hardware evidence is verified.
An agent run is one bounded, reviewed change with CI, not a calendar promise.
Before working, inspect issue status, dependencies and prior/ongoing PRs.

For each child issue: use the existing module/CLI where possible; write
independent nominal, adversarial and negative tests; run existing full
offline CI and strict MkDocs on the exact PR HEAD; update the canonical
status and corresponding protocol. Never infer bipedal locomotion, a
safe camera viewpoint or paper-ready results from synthetic proxies.

## Relationship to other ARC work

[ARC-RGBT](https://github.com/MatPomGit/arc-rgbt) studies multimodal sensing and fusion.
ARC-RVI studies target selection, acquisition geometry, coverage and documentation.
A future sensor exchange must preserve acquisition timestamps, native resolution,
calibration, frame conventions and file hashes. This is a proposed boundary;
no cross-repository runtime integration or shared dataset is implemented.

Reuse data only after checking provenance, rights, group-separated splits and overlap
between primary analyses. Keep each project's hypotheses and publication claims distinct.
Do not copy confidential source material or identities into public research artifacts.

## Execution

Use the existing controller and repository instructions. Registration is not a deployment
receipt or a new execution policy. Do not add another scheduler, task queue or merge path.
Run `python scripts/validate.py` and `python scripts/check_agent_docs.py`
before recording new software verification evidence.
Record exact revisions in PR evidence; physical results need independently traceable measurements.
