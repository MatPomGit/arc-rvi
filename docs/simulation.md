# Planar geometric simulation

Application version: 1.3.0

```bash
rvi simulate --scene simulation/worlds/planar_inspection.json --output results/simulation.json
```

The command evaluates the supplied route and writes a reproducible JSON report.
Existing output files are preserved. Invalid scenes exit with code 2. A rejected
route action is recorded in the report; the command still exits successfully.

## Model and interface

`PlanarSimulator` implements `SimulatorAdapter`: `reset()` restores the initial pose
and counters, and `acquire(CameraPose)` requests one move/turn/capture action.
Observations contain the actual pose, visible patch IDs, cumulative simulated time,
cumulative travel and any rejection reason. No device connection is opened.
The external physics connector `connect_simulator()` remains unavailable.

The model identifier is `planar_geometry_kinematics_v1`. World coordinates use metres:
+x is forward at yaw zero, +y is left, and positive yaw rotates counterclockwise.
Pose yaw and patch outward-normal angles use radians in `[-pi, pi]`.
The camera is located at the centre of a circular robot footprint.

Each action translates along a straight segment at constant linear speed, rotates
through the shortest yaw change at constant angular speed, then captures.
Translation, rotation and capture occur sequentially. The circular footprint does
not change during rotation. Movement is holonomic; there are no steering, gait,
stability, acceleration or articulated-body constraints.

## Independent analytic rotary-proxy reference (2026-10-29)

The test-only independent reference
`tests/unit/test_rotary_reference.py` checks the limited
rotation-screening model with an **analytic unit-circle arc versus
axis-aligned rectangle**. The reference does not call the
implementation's displacement-bound or adaptive subdivision logic.
It enumerates interval endpoints, circle/rectangle coordinate
crossings and stationary bearing angles, then computes the exact
minimum planar distance to the rectangle in the declared test
domain. Tests include positive collision despite clear endpoint
chords, near-corner contact, tangency within floating-point
tolerance, 1-micrometre near-miss and penetration, a distal
obstacle that can be excluded by the bound, and a zero-budget
unresolved result.

This is an **independent analytic oracle only for one unit-radius
planar revolute link at fixed base** (synthetic fixture, no robot
model confirmation). It does **not** validate arbitrary 3D
multi-joint motion, mesh collisions, finite-precision guarantees
outside the tested domain, uncertain real controller
interpolation or humanoid terrain safety. The broader adversarial
model validity task remains [#100](https://github.com/MatPomGit/arc-rvi/issues/100).

## Independent multi-axis 3D rotary reference (2026-10-29)

The test-only `tests/unit/test_rotary_reference_3d.py` extends the
independent comparison beyond the single-axis planar circle without
importing production FK matrices or the sweep derivative bound.

- A synthetic **two-revolute-joint gimbal** has the independently
  derived 3D tip position
  `(cos(yaw)*cos(pitch), sin(yaw)*cos(pitch), -sin(pitch))`
  in metres for a unit link. Tests compare this formula with the
  pinned-URDF FK at six fixed configurations, and build multiple
  intersecting/near-tangent 3D obstacle fixtures on the analytically
  known *interior* of linear joint interpolations.
- A **two-branch articulated tree** with independent z/y rotations has
  analytic endpoint tip separation `sqrt(2)*sin(1.4)` metres and
  a coincident pair of tips at the middle state. The corresponding
  explicitly listed self-sphere pair must be flagged between two
  individually nonoverlapping endpoint configurations.
- An **independent trigonometric interval enclosure** uses exact
  sine/cosine extrema and interval products to provide a sufficient
  clear-domain test for declared gimbal proxy/obstacle geometry.
  The interval oracle is separate from the production
  global-speed/Lipschitz bound, and is used alongside exact known
  interior contact examples. Its finite floating-point operations
  are not formal directed-rounding interval arithmetic.

The deterministic adversarial set includes six different paired
two-axis motions, an independently clear distant obstacle and
1-micrometre near-contact perturbations. All run without physics,
mesh imports, camera calibration or paid services. Passing these
tests does **not** validate arbitrary joint-tree geometry, every
numeric regime, true swept body meshes, moving floating base, real
controller interpolation, friction/foot dynamics or the actual
Unitree G1 EDU. Issue [#100](https://github.com/MatPomGit/arc-rvi/issues/100)
remains open until broader model-bound, property and numeric-domain
validation is independently reviewed.

## Numeric-domain and precision stress tests (2026-10-29)

The rotary proxy solver now rejects geometry and model scale above
1,000,000 m and rotary coordinate/accumulated travel above 100 rad
as `unresolved_invalid_bound`. Within its domain the clearance
test uses a ULP-based allowance proportional to scale and joint
count. These limits protect **software numerical reasoning**
rather than specify physical tolerances or a G1 EDU range.

The deterministic independent 3D analytic fixture suite now also
checks obstacle coordinates of 10^6–10^150 m, large continuous
angles, invalid/nonfinite FK bound metadata, and near-tangent
gaps and penetrations down to 10^-11 m. Values outside the domain
are **unknown**, not verified collision-free. This is not a
rounding-mode-certified proof across arbitrary URDF models or
physical sensor precision; #100 remains open for formal and
adversarial numeric review.

## Difficult-terrain and humanoid validity boundary (2026-10-28)

The present circular-footprint, planar, holonomic motion model **cannot**
represent Unitree G1 EDU bipedal stability, foot contact, surface traction,
stairs, gaps, loose rubble, falling, whole-body collision, torso/camera
motion from gait, or recovery after a disturbed step. An obstacle-free
planar path **is not** an executable humanoid trajectory. Static URDF
topology checks are also **not** dynamic/contact feasibility checks.

Before claiming safe or feasible inspection in difficult terrain, a
separate, validated simulator/robot adapter must provide a consistent
time-indexed state: base/torso pose, joint positions and limits, contact
locations and states, contact friction uncertainty, swept body geometry,
camera extrinsics/pose, observation quality and mission clock. It must
also provide independently checked support/contact constraints and a
reason for rejected or aborted motion. Planned footsteps, preflight
checks and the **executed** motion trace must remain separate.

A high-level planner may only use **declared observable** terrain and
camera information. Hidden contact truth, complete geometry and
accepted inspection coverage belong exclusively to the evaluator.
Unknown ground traction, model-out-of-domain terrain or an unverified
robot/camera setup is **not validated** (fail closed for any safety
claim); it is not automatically traversable. Existing preflight
rejections are not actual fall events or tested fail-safe hardware.

For scenario factors, independent reference and scope, see
[the terrain-factor registry](population.md), the
[study-specific P03 protocol](../experiments/exp03_viewpoint_planning/protocol.md)
and [physical safety](safety.md). No G1 EDU locomotion controller,
risk-rated friction coefficient or safe terrain threshold is currently
implemented or certified by ARC-RVI.

## Synthetic foot-support projection preflight

This is a **small, independently testable static geometry proxy**,
not an articulated inverse-kinematics model, force/contact solver,
or humanoid walking simulator.

Run the standard offline CLI with the synthetic neutral sample:

```bash
rvi stance --spec simulation/scenarios/static_support_example.json --output results/static_support.json
```

The spec declares one or two **assumed** horizontal foot-contact
polygons in metres, a common support height, a proposed horizontal
centre-of-mass projection and a required geometric boundary margin
in metres. The function forms the convex hull of contact vertices
and computes a signed minimum distance to its edges using a
deterministic analytic 2D geometry calculation. It rejects malformed,
non-convex or degenerate contact footprints, duplicate IDs,
non-finite numeric input and overwriting existing output files.
The report includes the exact input SHA-256 and
`evidence_type: synthetic_fixture`.

The only positive status is **`geometric_candidate_only`**. It
means *the supplied projected point is strictly inside the support
hull with the requested geometric margin*. It does **not** show
that gravity, joint torques, kinematics, terrain friction, joint
contact loads, slip avoidance, dynamic gait balance or robot
actuation are feasible.

Failures are recorded as
`outside_support_projection` or
`insufficient_static_margin`. Any declared
`steps`, `slope`, `loose`, or `unknown` terrain receives
`terrain_model_unsupported`. Contact state `unknown`
receives `contact_state_unknown`; different support heights
receive `noncoplanar_contact_unsupported`. In these cases
the report deliberately provides **no inferred support polygon
or margin**. No gait strategy or G1 EDU safety limit follows
from this fixture. The sample footprints are arbitrary test
geometry and **not** manufacturer foot dimensions.

### Coplanar 3D contact geometry (schema 1.1.0)

The same `rvi stance` CLI now accepts an **opt-in**, backward-compatible
`schema_version: 1.1.0` JSON file with 3D foot-sole vertex positions
(`footprint_xyz_m`), an assumed 3D centre-of-mass position
(`com_xyz_m`) and the existing required horizontal margin.

```bash
rvi stance --spec simulation/scenarios/sloped_support_example.json --output results/sloped_support.json
```

The synthetic example uses two foot polygons lying on **one shared tilted
plane** `z = 0.2*x`; it is not measured foot geometry or validated
robot mass distribution. The code fits a plane from three noncollinear
footprint vertices and verifies every other point lies within a
**synthetic numeric tolerance of 1e-8 m**. The vertical gravity line
through the supplied CoM intersects that plane at the same XY location.
The report includes plane slope (degrees), maximum normal residual (m),
support-plane height at the CoM projection (m), and geometric clearance
of the supplied CoM above that plane (m). Its signed support margin is
**the horizontal XY-projection distance in metres**, not a 3D
on-surface distance, a zero-moment-point margin or a friction cone test.

The 3D calculation only returns `geometric_candidate_only` when the
coplanar-contact assumption, declared terrain geometry, CoM-above-plane
condition and existing 2D geometric margin all pass. It reports
`noncoplanar_contact_unsupported` for differently elevated or
independently tilted contacts (including step geometries), and
`terrain_geometry_mismatch` for tilted coordinates declared as
`flat_horizontal`. `steps`, `loose`, `unknown` and
`unknown` contact state remain unsupported. The old 1.0.0 fixture
continues to reject `slope`; only schema 1.1.0 can geometrically
represent a **single assumed sloping plane**. Unknown friction,
nonrigid footing, sliding, force distribution, articulated motion and
time-varying balance remain **unmodelled** and therefore no physical
safe-traversal inference follows from a positive result.

The model does not couple to the planar route planner or a robot
adapter. Before difficult-terrain planning can use this check,
develop independently verified articulated kinematics and body
geometry, actual terrain/contact observations, ground reaction
constraints and time-indexed slip/retreat/abort dynamics.
See [study P03](../experiments/exp03_viewpoint_planning/protocol.md)
and [safety](safety.md).

## Visibility and coverage

Each surface patch has a representative point, outward normal and positive area weight.
A patch is visible when all these conditions hold:

- Its point is within the inclusive camera minimum and maximum range.
- Its bearing is within half the horizontal field of view about the camera yaw.
- Its outward normal faces the camera within `max_incidence_rad`.
- The camera-to-point segment does not intersect a circular obstacle.

A point coincident with the camera is not visible. Angular comparisons allow
`1e-12` radians of numerical tolerance. Obstacle intersection includes tangency
and expands the radius by `1e-10` metres for conservative numerical comparisons.
Only explicit obstacles occlude; patch-to-patch self-occlusion is not represented.

`sampled_surface_coverage` is the sum of area weights of observed patches divided
by total declared area weight. Repeated observations count a patch once.
Visibility of a representative point assigns its whole patch weight. This is a
sampling approximation, not polygon clipping or an exact visible mesh-area measure.
Refine the patch sampling before interpreting area estimates on a real surface.
The geometric model does not generate images or measured sensor signals. The
separate **uncalibrated planar feature generator** in `rvi.perception` adds
synthetic horizontal pixel locations, range estimates, brightness and sharpness
proxies, and seeded sensor noise/dropouts. It does not render images.

## Collision, budget and termination

For motion, each circular obstacle is expanded by the robot footprint radius.
The minimum distance from its centre to the entire move segment determines collision,
including both endpoints. An intersecting initial footprint is an invalid scene.

The simulator first checks whether the complete action fits the time budget, then
checks its swept footprint. It rejects an action with `time_budget_exceeded` or
`path_collision`. A rejected action consumes no partial distance or time and captures
nothing. Previous accepted coverage remains. Reset before making another request.
These are preflight rejections, not simulated impacts or partially executed motion.

Time equals segment length / linear speed + shortest yaw change / angular speed
+ capture duration. An exact budget boundary is accepted, allowing at most eight
floating-point ULPs of accumulated rounding slack. Reported time is not clamped.
Elapsed time is model time, not measured CPU runtime.

Route evaluation stops on the first rejection. `route_complete` means every supplied
action was accepted. `coverage_complete` independently indicates that all declared
patches were observed. An empty route completes with zero coverage and zero time.
`status: completed` describes route execution, not successful inspection.

## Scene and report

The example scene specifies schema `1.0.0`, `evidence_type: simulation`, a start pose,
camera parameters, motion parameters, obstacles, patches and a route.
Unknown or missing fields, non-finite numbers, boolean numeric parameters, invalid
ranges, nonpositive speeds/areas/radii and duplicate patch IDs are rejected.
Robot radius and capture duration may be zero. The time budget may be zero.

Each report records its scene SHA-256, model ID and shared package/runtime provenance.
Each observation includes its step number, requested pose and actual pose.
Input files and matching source snapshots are required to archive a reproducible run.
The report is a deterministic model evaluation; it has no wall-clock timestamp or
independent replicate ID. It does not implement the full experimental run contract.

The included scene has patches of 1 and 3 square metres and one occluding circle.
The initial capture observes only the first patch. Moving one metre laterally reveals
the second. With 1 m/s travel and 1 s per capture, the route takes 3 s and travels 1 m.
The analytic tests also check angle wrap, incidence/range boundaries, tangent occlusion,
mid-segment collision, weighted coverage, partial outcomes and action timing.

For a local developer-level synthetic feature check:

```python
from rvi.adapters.simulator import load_scene
from rvi.perception import load_sensor_config, simulate_sensor
from pathlib import Path

scene, _ = load_scene(Path("simulation/worlds/planar_inspection.json"))
settings, _ = load_sensor_config(Path("simulation/conditions/sensor_exploratory.json"))
policy_observation, evaluator_truth = simulate_sensor(scene, scene.start, settings)
```

Only `policy_observation` may be passed to an algorithm. `evaluator_truth`
retains ground-truth patch identities and ideal geometric visibility exclusively
for evaluation. The projection uses a **1D horizontal pinhole approximation**:
`u_px = width_px * (0.5 - relative_bearing_rad / horizontal_fov_rad)`.
`+y` is camera-left, so pixel coordinates increase toward camera-right. Range
noise is expressed in metres, pixel noise in pixels; light/exposure/focus/blur
factors are **dimensionless synthetic proxies**, not physical or measured image
quality. Independent SHA-derived seeded streams preserve matched perturbations
between factor settings. Missing frames and undetected patches remain explicit.

No physical sensor calibration, target recognition, true image production, or
unknown-surface inference is established. The existing benchmark still uses
known-geometry visibility and is **not** sensor-conditioned. See Issue #17
for the unfinished full sensor model and calibration gates.

Candidate selection is connected through the [paired geometric benchmark](benchmark.md).
Next: generate paired scene conditions and disjoint geometry families. Physics/sensor calibration is required before transferring this model
to an articulated or physical robot study.
