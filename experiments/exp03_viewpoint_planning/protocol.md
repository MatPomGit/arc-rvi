# Study 03: Whole-Body-Aware Viewpoint and Path Planning for Humanoid Visual Inspection

Protocol version: 1.1.6

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

## Initial static support proxy (fixture-only, 2026-10-28)

The offline `rvi stance` command checks whether a synthetic
centre-of-mass projection lies strictly inside the convex hull of
one or two assumed horizontal foot contacts with a declared margin.
It preserves source SHA-256 and explicitly rejects unsupported
slopes, steps, loose/unknown terrain, noncoplanar foot heights and
unknown contact state. This adds a regression-tested geometric
**screening proxy** for a flat, stationary stance, not a
humanoid dynamic support, contact-force, gait, IK or collision
constraint. Do **not** include this score in an executed
inspection-coverage result or imply it makes Unitree G1 EDU safe
to traverse difficult ground. Full #25 acceptance remains open.

## Coplanar 3D contact fixture upgrade (2026-10-28)

The offline `rvi stance` preflight adds schema `1.1.0` for two
assumed 3D foot-contact polygons on **one coplanar sloping surface**
and an independently provided CoM position. Analytic checks now
return a vertical-gravity XY-projection margin, plane slope and
noncoplanarity residual. Differently elevated footholds, steps,
deformable terrain and unknown friction remain outside this limited
model. The numeric plane tolerance is a fixture precision check,
**not** an allowable rough-terrain contact error for actual hardware.

This is an incremental geometric prerequisite for #25 only, not
inverse kinematics, whole-body collision, force closure or dynamic
walking stability. The G1 EDU variant/sensor mount are still
unverified, and no new physical trials or inspectable viewpoints are
declared feasible. The primary joint-versus-decoupled inspection
estimand is unchanged.

## Joint-configured URDF FK audit (2026-10-28, unfrozen)

The `rvi robot-model --joint-state` option now computes *forward*
transforms from a hash-pinned local URDF and a complete, finite,
in-range joint-state fixture. Unlike the earlier zero-only preflight,
it can calculate a **candidate virtual camera pose** under a chosen
joint configuration, and rejects missing or out-of-limit joint states.
The virtual floating base is still fixed at an assumed identity pose.
A correct FK result is **not** proof that a humanoid can attain that
configuration: it does not validate inverse kinematics, the stance
contact distribution, whole-body collision, fall margins or motion
along a trajectory.

P03 must retain unsupported/unvalidated collision, support and
dynamics as separate blocking gates. Before generating feasible
inspection viewpoints from a delivered G1 EDU model, obtain verified
variant-specific URDF bytes, model-body dimensions, sensor extrinsics,
independent FK cross-check and a scene/terrain collision reference.
Do not substitute a toy analytic chain for the actual robot model.

## Synthetic FK-linked collision proxies (2026-10-28, unfrozen)

The optional `rvi robot-model --collision-fixture` audit now
checks **explicit, static** spherical envelopes attached to
configured URDF link frames against declared static 3D
axis-aligned obstacles and enumerated self-sphere pairs. Signed
clearance accounts for the declared test margin, and a touching
proxy is a positive overlap detection.

A clear result **must not** be treated as whole-body
collision-free. The fixture can omit the torso, feet, swinging
arms or any other link; only explicitly listed self-pairs are
checked. No swept trajectory, environmental map uncertainty,
terrain/contact dynamics, robot-specific collision mesh or real
G1 EDU calibration is present. Keep full-body collision and
locomotion feasibility as blocking P03 evidence gates until
independently verified against the delivered articulated model.

## Reference model preparation (exploratory)

The planned Unitree G1 EDU embodiment will use a version-pinned,
manufacturer-provided URDF **only after** its actual machine variant has
been identified. An [offline model audit](../../docs/architecture.md) now
checks imported joint-tree consistency, numeric limits and static
zero-joint camera-frame transforms. The source-audit supports the virtual root `floating` joint using an
explicit identity-base convention only, not physical base localization.
User-supplied G1 material proposes staged read-only telemetry and TF2
checks before control; P03 must first verify `mode_machine`, camera and
LiDAR extrinsics and pose synchronization against independent references.
The source examples do **not** prove functioning G1 ROS 2 controllers.
It does **not** implement articulated
collision/reachability, full forward/inverse kinematics, stability or
actual G1 physical verification. Issue #25 remains open.

## Difficult-terrain humanoid feasibility stratum (unfrozen)

The mobile platform is a **bipedal humanoid**, not a holonomic circle.
A view candidate is provisionally executable only if a continuous
**whole-body** trajectory can reach and maintain an appropriate stance:
valid foot support, contact/friction feasibility, full-body/self-collision
clearance, reachable camera pose, stable turning and a feasible escape
route, within the time budget. `unknown_contact`, unavailable contact
reference and out-of-model geometry mean **unverified feasibility**, not
safe traversal. A pose reached by teleoperation, when no equivalent
autonomous control exists, is not autonomous evidence.

Cross terrain layout (level, stairs/raised edges, inclined or loose
support, cluttered narrow passage, sparse support) with target-view
height, lighting and traversability sensing error **only within the
independently validated model envelope**. Pair all methods on identical
initial stance and observations. Compare geometric routing, contact-aware
routing, imaging-quality-aware routing and the coupled version, retaining
the primary joint-versus-decoupled estimand already defined above.
Record unsuccessful foot contacts, slip warnings, planner failure,
safety abort, camera obstruction and omitted/blurred frames separately;
a planned image counts zero until actually captured and accepted.

The selected Unitree G1 EDU needs verified joint/foot dimensions,
contact model, actual camera mounting, controller interface, and
external pose/terrain reference before such claims. Other published
G1 rough-terrain policies **do not** establish those parameters.
The current planar simulator does not implement these constraints;
do not execute a confirmatory comparison with synthetic terrain
labels. See [terrain registry](../../docs/population.md) and
[hardware safety](../../docs/safety.md).

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 03](../../papers/paper03/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Literature-derived humanoid ablation (unfrozen)

The [literature intake](../../docs/literature.md) motivates an additional
whole-body-aware versus fixed-base/manipulator-adapted feasibility ablation.
Keep candidate views, budget and independent collision/stability oracle
identical, and record infeasible views and planning overhead. This is
**secondary to the prespecified joint-versus-decoupled primary contrast**;
adding an illustrative humanoid model is not evidence of stability or
physical executability. Do not transplant predicted t statistics from
unverified draft hypotheses into a result or power claim.

## Prior-art qualification, 2026-10-27

The publisher record for [RoboInspect (Wang et al., 2026)](https://doi.org/10.1016/j.cacaie.2026.100007)
documents physical humanoid navigation and crack-inspection case studies.
A claim that humanoid autonomous inspection has **never** been validated
physically would be false. Study 03 instead proposes a narrower, independently
testable difference: coupled feasible viewpoint/motion selection under a
common validated motion budget, with explicit whole-body/stability checks.
No novelty or improvement claim is established until reproducible
method-by-method evaluation and full prior-art review.

## Additional comparator gate: photometric + kinematic + routing prior art (2026-10-28)

The institutional [doctoral-thesis record of Staderini (2026)](https://repositum.tuwien.at/handle/20.500.12708/226537)
reports integrated viewpoint generation with **photometric visibility,
kinematic pose feasibility and inspection-route optimisation** plus
synthetic/physical evaluations (3/6/8 DoF systems). This overlaps with the
proposed P03 coupling of feasibility, imaging and motion. Its abstract does
not supply independently extractable numeric effect sizes, and it may
share data with [Staderini et al., IROS 2024](https://doi.org/10.1109/IROS58592.2024.10802791).
Do **not** count these two outputs as independent validations without a
study-level overlap audit.

**Pre-confirmation baseline decision:** in addition to the primary
joint-versus-decoupled matched comparison above, specify and validate a
**strong joint quality/kinematics/route comparator** representative of
existing methods. Use exactly the same feasible camera poses, safety
oracle, planner deadlines and accepted-coverage evaluator where possible;
label any approximation to the published algorithm explicitly. A
heuristic reconstruction is **not** an external-method replication. This
is an unfrozen baseline requirement, not evidence of a whole-body result.

The [Bettles et al. preprint](https://arxiv.org/abs/2603.16471)
already reports physical mobile-manipulator NBV inspection with uncertain
obstacles; its abstract does not establish a verified independent
surface-coverage denominator. ARC-RVI must compare *executed* accepted
views rather than planned visibility alone. Full sources and evidence
levels are tabulated in the [critical review](../../docs/prior-art-critical.md).

## Direct comparative baselines and reported evidence

[Staderini et al. (IROS 2024)](https://doi.org/10.1109/IROS58592.2024.10802791)
already combine camera geometry and robot kinematics for feasible inspection
viewpoints. [Gemerek et al. (2022)](https://doi.org/10.1109/TRO.2022.3180628)
address directional sensing with occlusions. The [Bettles et al. (2026)
preprint](https://arxiv.org/abs/2603.16471) reports **physical trials** on a
mobile manipulator in a confined pipe-network mock-up with online geometric
estimation. In contrast, [Ghaleb et al. (2026)](https://doi.org/10.3390/machines14090980)
report numerical and Gazebo testing, **not physical humanoid trials**.
The primary proposed difference is a validated Unitree G1 EDU whole-body,
balance-aware **coupled** viewpoint/motion plan under a common budget,
not novelty for generic kinematics-aware view planning, NBV in clutter or
hardware inspection. Full methods review remains outstanding.
