# Study 03: Whole-Body-Aware Viewpoint and Path Planning for Humanoid Visual Inspection

Protocol version: 1.1.0

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does joint view and route selection increase valid surface coverage under a common
mission budget compared with decoupled coverage and routing?
Use the same candidate set and feasibility oracle for the primary comparison.

Proposed hypothesis: Joint planning increases valid coverage relative to decoupled planning at the same mission budget.

## Design and baselines
Vary object geometry, passage width, camera reach and permitted stance locations.
Express dimensions in metres and joint limits in radians. Use geometry families
held out from parameter tuning, with paired scenes and starts across methods.

Compare fixed shot order, nearest-neighbour travel, greedy set cover followed by a
route heuristic, and joint view/path planning. Name the actual route heuristic;
do not describe a heuristic as an exact travelling-salesperson solver.
The existing planar greedy planner is an additional low-information reference.
Ablate kinematic feasibility and travel cost one at a time.

## Endpoint and failure
The primary endpoint is area-weighted valid coverage at the frozen mission deadline.
A covered triangle must meet line-of-sight, distance, incidence and image-quality
requirements. Count overlapping views once. Use the common surface definition in
[the analysis plan](../analysis/README.md).

Count unsuccessful missions in the primary denominator. For a collision or stability
violation, retain only coverage accepted before termination; also report an all-zero
failure sensitivity analysis and violation rate. Never score an unexecuted planned
view as acquired coverage. Planning timeout consumes the same mission budget.
Report executed distance, planning latency, infeasible proposals and success separately.

## Unit, analysis and acceptance
The independent unit is an object/environment instance, clustered by geometry family.
Estimate paired coverage differences; use family-clustered intervals.
Cost-coverage curves are secondary and must use predeclared budgets.
Freeze the camera model, collision margin, stability criterion, timing model and
budget before confirmation. Validate each with analytic test scenes.
Whole-body claims require a verified articulated model; planar fixtures are insufficient.

## Reference model preparation (exploratory)

The planned Unitree G1 EDU embodiment will use a version-pinned,
manufacturer-provided URDF **only after** its actual machine variant has
been identified. An [offline model audit](../../docs/architecture.md) now
checks imported joint-tree consistency, numeric limits and static
zero-joint camera-frame transforms. It does **not** implement articulated
collision/reachability, full forward/inverse kinematics, stability or
actual G1 physical verification. Issue #25 remains open.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 03](../../papers/paper03/manuscript.tex).
Publication boundaries: [research program](../README.md).
