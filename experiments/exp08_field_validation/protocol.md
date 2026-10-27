# Study 08: Experimental Evaluation of Autonomous Humanoid Robots for Standardized Visual Documentation

Protocol version: 1.1.0

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
