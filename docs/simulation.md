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
