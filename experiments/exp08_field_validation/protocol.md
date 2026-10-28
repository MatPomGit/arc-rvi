# Study 08: Experimental Evaluation of Autonomous Humanoid Robots for Standardized Visual Documentation

Protocol version: 1.1.1

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Is autonomous documentation non-inferior to standardized manual documentation in valid
coverage, while changing variability, duration or intervention requirements?
Non-inferiority concerns coverage only; do not infer equal speed or effort.

Proposed hypothesis: Autonomous coverage is no lower than manual coverage minus the justified non-inferiority margin.

## Design and baselines
Use an object/session crossover with randomized balanced method order.
Compare manual acquisition using the same required shot list, a static robot plan
when feasible, and the integrated autonomous workflow.
Use the same camera and quality criteria where feasible; record unavoidable setup
differences. Cross several operators with several objects and sessions.
Prevent operators from seeing earlier results before their own acquisition.

Assign coded acquisition packages to assessors blinded to method where possible.
Remove method metadata and randomize package order. Record whether blinding was
successful. Obtain independent duplicate ratings for a predeclared subset and report
agreement under a frozen adjudication rule.

## Endpoint and failure
The primary endpoint is the paired difference in valid required-region proportion:
autonomous minus manual. Required regions have equal weight in this study's shot list;
this endpoint differs from mesh-area coverage in studies 03, 04, 06 and 07.
Freeze an absolute non-inferiority margin with task-based justification before collection.
Claim non-inferiority only if the lower bound of the predeclared 95% interval exceeds
minus that margin. Do not choose the margin from confirmation results.

Timeouts, interventions and incomplete packages remain in the assigned-method analysis.
Report valid regions actually acquired, mission completion, human intervention count
and duration. A separate complete-case analysis is a sensitivity analysis only.

## Unit, analysis and acceptance
The independent unit is an object/session block; operators and repeated images are
crossed or nested factors. Plan sample size for the margin and clustering after the
pilot. Use a paired model that accounts for object, operator and period effects;
freeze the exact model and missing-data rules before confirmation.

Requires an integrated physical system, an approved operating procedure, data rights
and an institutional determination of applicable human-participant requirements before
operator recruitment. The main inference concerns end-to-end documentation, not the
mechanistic effects assigned to earlier papers.

## Difficult-terrain mission and safety denominator (unfrozen)

The candidate claim concerns **end-to-end humanoid inspection
documentation in challenging access**, not a demonstration
that the robot can walk on a nominal indoor map. Stratify
planned paired manual/autonomous tasks by independently
assessed accessibility: level route, stairs/steps, constrained
passage and complex footing **only within a separately
approved physical risk envelope**. The tested G1 EDU
variant, fall zone, traction/support uncertainty and
emergency takeover must pass the site safety gate first.
Do not recruit humans or deliberately induce falls/slips
as an informal field test.

Predeclare each method's reachable required regions. An
unsafe/unreachable region cannot be removed **after**
assignment to improve noninferiority, nor can a human
operator silently rescue the autonomous arm without
counting intervention. Keep aborted missions, assistive
takeover, omitted images, contact instability and safety
stops in the assigned-method denominator and report
feasible-coverage stratum and whole-mission success
separately. A comparison over flat, supervised corridors
must not be generalized to stairs, rubble or unverified terrain.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 08](../../papers/paper08/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Prior-art boundary, 2026-10-27

[RoboInspect (Wang et al., 2026)](https://doi.org/10.1016/j.cacaie.2026.100007)
reports physical humanoid inspection demonstrations in an indoor
infrastructure setting. This proposal therefore does **not** claim
the first physical humanoid autonomous inspection system.
Its distinct intended contribution is a **prespecified, assessor-blinded
noninferiority comparison against standardized manual documentation**
under independent object/session blocks, a clinically or operationally
justified margin and signed safety/measurement approvals. Such evidence
is not yet collected in ARC-RVI.

## Prior human-versus-technology experiments (2026-10-27)

[Aust & Pons (2022)](https://doi.org/10.3390/app12042250) compared humans with
image processing, AI and 3D scanning during engine-blade inspection; this
was not a humanoid-robot comparison. [Xia et al. (2022)](https://doi.org/10.1061/(ASCE)CO.1943-7862.0002322)
benchmarked human versus robot performance in a **simulated** emergency
structural inspection task. Alongside RoboInspect, these establish that broad
claims of the first human-versus-automation inspection study are not justified.
The distinct intended test is physical, paired, assessor-blinded inspection
**documentation** against manual capture, with a frozen noninferiority margin,
common tasks and independent reference quality metrics.

## Actual field precedents and boundary of manual comparison

[Kim et al. (2022)](https://doi.org/10.3390/drones6110355) report a bridge
inspection field comparison of human inspection with UAS acquisition;
[Gehring et al. (2021)](https://doi.org/10.1007/978-981-15-9460-1_18)
report **offshore field testing** of quadruped ANYmal;
[Seppänen et al. (2022)](https://doi.org/10.1007/s10846-022-01711-3)
report mobile-robot prototype comparisons for delay-affected
**teleoperation** rather than assessor-blinded image documentation.
These precedents preclude general 'first physical robotic inspection' or
'first human comparison' claims. The proposed original endpoint, if
validated, is balanced manual versus humanoid **documentation quality**
under a frozen noninferiority margin and independent judges.
