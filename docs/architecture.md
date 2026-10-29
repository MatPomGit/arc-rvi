# Architecture

For the primary operational scenario, see [commanded car / bumper photography and return-to-human](vehicle-inspection-missions.md). It specifies a fail-closed target/part-resolution contract, reflective car-body image acceptance and an operator-verified return. The implemented evaluator is **offline fixture-only**; no physical robot motion or sensor is controlled.

The shared core contains neutral algorithms and data contracts. A future
orchestrator will connect target localization, navigation, viewpoint selection,
acquisition, quality control and evidence generation via one adapter boundary.

1. Confirm a target identifier.
2. Localize the target and its required visual regions.
3. Determine candidate viewpoints and feasible routes.
4. Execute movement only through a validated safety-controlled robot adapter.
5. Acquire images and evaluate measured quality.
6. Replan/retry if quality or coverage is insufficient.
7. Store a versioned package of images, hashes, provenance and outcomes.

## Offline reference-model preflight

The selected Unitree G1 EDU requires identification of the **particular
machine variant** before choosing a URDF. The manufacturer publishes several
23- and 29-joint G1 descriptions, distinguished by the device
`mode_machine` identifier. The source reference is
[Unitree's G1 description repository](https://github.com/unitreerobotics/unitree_ros/tree/7919cba47a3f68888f3b084945b0ffbf3bb3763a/robots/g1_description)
at commit `7919cba47a3f68888f3b084945b0ffbf3bb3763a`.
The two locally supplied sources, *Podstawowy opis Robota Unitree G1 EDU*
(section 1) and *Instrukcja programowania robota humanoidalnego Unitree
G1 EDU*, v1.8 (sections 2, 5–6, 10–11), describe a candidate **29-DOF**
configuration with an Intel RealSense D435i, Livox MID360, four microphones,
a developer computer and a separate low-level locomotion controller.
These are **document claims**, not a verified inventory, firmware profile,
URDF choice, measured sensor specifications or calibrated TF transforms.
The official G1 description index distinguishes 23-/29-DOF variants by
`mode_machine`; obtain that identifier from the actual robot before
selecting assets. ROS 2/DDS is a potential integration boundary only:
the teaching manual's example topic names, driver nodes, IP settings and
code snippets are illustrative, not a deployed or tested G1 interface.
In particular, `unitree_guide` discussed in the short description
targets quadruped examples and is not a validated G1 driver.

The user additionally supplied three laboratory photographs (2026-10-27)
showing an upright robot which the user identifies as G1 EDU. A segmented
hand-shaped end effector, silver articulated limbs, dark head housing,
body straps and a nearby wheeled structure are visible. These observations
confirm the *visual documentation of an available laboratory platform*,
**not** its 29-DOF layout, exact revision, camera/LiDAR models, protective
harness certification, SDK connectivity or measured movement. The photos
remain outside the public repository. The next identification step is an
operator-approved **read-only** hardware/firmware and `mode_machine`
inventory, followed by matching and auditing the manufacturer's URDF.

### Read-only SSH hardware inventory

Run `scripts/inspect_robot_ssh.py` through SSH on the robot's **developer
computer** without copying or installing anything on the robot. On your
local Linux workstation, from the repository root:

```bash
# Passive inventory first; the output file is stored LOCALLY.
(umask 077; ssh -T USER@ROBOT_HOST 'python3 -' \
  < scripts/inspect_robot_ssh.py > g1_edu_inventory.json)

# Once the DDS network interface is known (e.g. eth0), optionally request
# only one rt/lowstate message, bounded to nine seconds:
(umask 077; ssh -T USER@ROBOT_HOST 'python3 - --dds-interface eth0' \
  < scripts/inspect_robot_ssh.py > g1_edu_inventory_dds.json)
```

The script only inspects OS/Python/ROS/SDK versions, interface names and
link state, USB vendor/product IDs **without serials**, video and IIO
device names and a few known local URDF directories with file SHA-256.
The DDS option uses a temporary **subscriber only** for
`rt/lowstate` to collect `mode_machine`; no command topic, motion or
SDK install. The tool intentionally omits passwords, hostnames,
serial numbers, IP/MAC addresses and raw IMU/motor readings.
An Ethernet LiDAR may not appear in USB enumeration; missing devices
or packages in this report do **not** prove they are absent.

If DDS shows `sdk_or_dds_error`, use the existing onboard Python
environment where `unitree_sdk2py` is already installed, or first
review the passive interface list. Do not change network, firmware,
ROS 2 configuration or robot operating mode merely to run this inventory.
The numeric `mode_machine` must still be matched against a **pinned**
official Unitree description revision and the physical hand/sensor
installation separately. Keep local JSON reports out of public Git
and review them before sharing.

The exact hardware variant is **not yet known**. Do not assume a 29-DoF
robot, a D435 camera, particular joint limits or a calibrated camera mount.

With a locally obtained URDF from the matching manufacturer revision,
calculate its **SHA-256 independently** and run (no network, simulator,
dependencies or robot required):

```bash
rvi robot-model --urdf /path/to/selected.urdf --expected-sha256 YOUR_SHA256 --camera-frame YOUR_VERIFIED_URDF_LINK --output results/robot_model_audit.json
```

The audit rejects changed/untrusted bytes, invalid topology, unsupported joint
types, degenerate axes and invalid joint bounds. It supports one virtual root `floating` base joint, as found in
the upstream G1 URDF; it assumes the virtual base is at its identity pose
and **does not infer the robot's physical world pose**. It reconstructs the zero-joint
tree transforms and checks whether a specifically requested camera link exists.
An unknown camera frame is **not** silently replaced by a guessed transform.
The output is `evidence_type: fixture`: static source consistency only.
This is not inverse kinematics, stability, collision, gait, hardware
calibration or physical authorization. The original vendor URDF/meshes and
their license remain with the upstream source, outside this repository.

A separate offline **synthetic static foot-support preflight** is
available through `rvi stance --spec simulation/scenarios/static_support_example.json
--output results/static_support.json`. It uses assumed horizontal contact
polygons and centre-of-mass projection only, not actual robot mass modelling
or whole-body kinematics. Its sole positive status
`geometric_candidate_only` means a polygon projection passes a
caller-declared boundary margin. Steps, slopes, loose/unknown terrain,
unknown contacts and different foot heights are unsupported or unverified.
This is a bounded first contribution to issue #25, **not** a dynamic
bipedal stability or G1 EDU inspection-validity oracle; see
[simulation](simulation.md).

### Configured offline forward kinematics (fixture-only)

The existing `rvi robot-model` command also accepts a caller-supplied,
bounded, local JSON configuration of **all** movable URDF joints:

```json
{"schema_version":"1.0.0","joint_positions":{"arm_joint":0.25}}
```

```bash
rvi robot-model --urdf /path/to/pinned_model.urdf \
  --expected-sha256 PINNED_64_CHARACTER_LOWERCASE_HEX \
  --camera-frame VERIFIED_URDF_LINK \
  --joint-state /path/to/joint_state.json \
  --output results/configured_fk.json
```

The example key `arm_joint` is **illustrative**, not a G1 joint. A real
input must name **every** movable joint declared by the selected URDF
(revolute in radians, continuous in radians and prismatic in metres).
Unknown, omitted, extra, non-finite or out-of-limit joint values are
rejected, without assuming unspecified joints are at zero. A one-root
floating joint retains the explicit **virtual identity-base assumption**,
not a physical base pose. The command preserves the prior zero-pose
audit and adds source-hashed `configured_joint_pose` for every link.

The FK uses URDF joint origins and normalized axes; analytic fixtures
cover a revolute joint followed by a prismatic joint, camera offsets,
boundary values and a floating root. This is **only offline articulated
forward kinematics**. It does **not** solve inverse kinematics, check
joint torque/velocity, self/environment collisions, foot contacts,
dynamic balance, sensor calibration or physical safety. Even when a
configured camera frame exists, its real extrinsics remain unverified
until the actual Unitree G1 EDU variant and sensor mount are confirmed.
The output must **not** be used as an executable or safe stance approval.

### Offline collision-proxy preflight (fixture-only)

The same offline FK command accepts an **optional**, bounded JSON
collision fixture with spheres bound to named URDF links, static
axis-aligned boxes in the same (assumed virtual) root frame, and
**explicit** pairs of sphere IDs for local self-proxy checks:

```json
{
  "schema_version": "1.0.0",
  "clearance_margin_m": 0.01,
  "spheres": [
    {"id":"camera_envelope","link":"camera",
     "center_local_m":[0,0,0],"radius_m":0.1}
  ],
  "boxes": [
    {"id":"beam","min_xyz_m":[0.5,0.8,0],
     "max_xyz_m":[1.0,1.0,1.8]}
  ],
  "self_pairs": []
}
```

```bash
rvi robot-model --urdf /path/to/pinned_model.urdf \
  --expected-sha256 PINNED_64_CHARACTER_LOWERCASE_HEX \
  --joint-state /path/to/joint_state.json \
  --collision-fixture /path/to/collision_fixture.json \
  --output results/collision_proxy_audit.json
```

The placeholder link name and dimensions above are **synthetic**,
not Unitree G1 EDU body geometry. The command requires a complete
configured joint state, transforms each explicitly supplied sphere
by offline FK and reports signed sphere-to-AABB and specifically
listed self-sphere clearances. Touching counts as overlap. It
rejects missing URDF links, duplicate IDs/pairs, non-finite
values, malformed boxes and unbounded inputs. The fixture SHA-256
is included in the output.

**`no_proxy_overlap_unverified` means only that the supplied
static proxies do not overlap the supplied static boxes or
explicit self-pairs** at one assumed joint configuration.
Missing links, omitted volume, all unlisted self-pairs, moving
obstacles, foot contact, body dynamics, motion swept volume and
real robot geometry are **not** checked. Output always declares
`full_body_collision_validation: not_performed` and
`trajectory_sweep_validation: not_performed`. Never use this
preflight to clear physical robot motion or certify whole-body
collision safety. See [P03 protocol](../experiments/exp03_viewpoint_planning/protocol.md)
and [safety](safety.md).

### Offline waypoint collision diagnostics (fixture-only)

The canonical `rvi robot-model` command can review **2–32**
time-ordered joint configurations using a local UTF-8 JSON trajectory:

```json
{
  "schema_version": "1.0.0",
  "waypoints": [
    {"time_s": 0, "joint_positions": {"slider": -1.0}},
    {"time_s": 1, "joint_positions": {"slider": 1.0}}
  ]
}
```

The joint name is illustrative. Every waypoint must contain the
**complete** set of joints declared movable by its own pinned URDF,
with radians for rotary and metres for prismatic joints; timestamps
must be strictly increasing. Use:

```bash
rvi robot-model --urdf /path/to/pinned_model.urdf \
  --expected-sha256 PINNED_64_CHARACTER_LOWERCASE_HEX \
  --trajectory /path/to/trajectory.json \
  --collision-fixture /path/to/collision_fixture.json \
  --output results/waypoint_collision_audit.json
```

`--trajectory` and `--joint-state` are mutually exclusive; the
collision fixture is mandatory for a trajectory. Inputs are local,
size-bounded, source-hashed, and output is never overwritten.
At each waypoint, static FK-attached sphere proxies are checked
against explicit static AABBs and listed self-pairs. For each pair
of adjacent waypoints, a straight segment connecting the sphere
centres is screened against an **axis-wise sphere-inflated box**.
This chord screen conservatively flags possible contact for **that
straight chord** (and may over-flag corners), but the actual centre
path of an articulated joint is generally **curved**. The chord
check can therefore **miss a collision on the true swept path**.

The diagnostic statuses are:

- `proxy_overlap_at_waypoint`: collision proxy touches or overlaps
  a declared obstacle or self-pair at a supplied configuration.
- `possible_chord_obstacle_overlap`: no sampled overlap, but the
  straight centre chord intersects an expanded obstacle box.
- `sampled_proxy_clear_between_samples_unverified`: no overlap
  among the **supplied** sampled proxies and chords; the actual
  intermediate FK trajectories and full robot remain **unverified**.

The latest fixture-only preflight also classifies segments using the
**declared URDF joint types**. If **all revolute and continuous joint
positions remain unchanged** between adjacent waypoints, and only
prismatic joints change, then under **linear joint interpolation and
fixed virtual base**, each proxy-sphere centre follows an *exact affine
line*. The inflated-AABB chord screen can then conservatively rule out
obstacle contact for **only those explicit proxies and obstacles**.
Explicit self-sphere pairs are additionally checked along their
relative centre-line, including contacts missed by both endpoints.
No unlisted link/box or self-pair is evaluated.

- `affine_proxy_sweep_clear_unverified_body`: no contact in the **declared
  proxy subset** under the stated prismatic-only, linearly
  interpolated motion; it does **not** clear the actual robot.
- `affine_self_proxy_overlap_candidate`: an explicitly selected
  sphere pair touches or overlaps between affine waypoints.
- `rotational_sweep_unresolved`: a revolute or continuous joint changed
  and neither endpoints nor centre chords exposed contact. Real
  articulated paths can curve into an obstacle, so this is **not clear**.

### Bounded rotary proxy-sweep screening (schema 1.0.0 output)

The offline trajectory auditor now also performs an adaptive
**fixed-virtual-base, linearly interpolated joint** screen for declared
link-attached collision spheres. Its conservative global upper bound
on sphere-centre travel is derived from the pinned URDF's sum of
joint-origin translation lengths, the maximum absolute interpolated
prismatic positions, local sphere-centre offsets, and the total
joint-angle/prismatic variation over the segment. This intentionally
overestimates the distance that any declared sphere centre can move.

If every supplied signed proxy–obstacle and explicitly checked
self-pair clearance at a subinterval's starting state exceeds the
maximum possible travel over that entire interval (including a
small numerical allowance), this **proxy subinterval** can be
excluded from contact under the *declared interpolation and fixed-base
assumptions*. Otherwise an intermediate FK state is evaluated and
the interval subdivided, up to a bounded **total budget of 64
additional FK evaluations** by default. Users may set
`--rotary-evaluations N` on `rvi robot-model --trajectory`, where
`0 <= N <= 128`; exhausting the budget yields
`rotary_sweep_unresolved`, **never a clear**.

Intermediate proxy overlap produces
`proxy_overlap_between_waypoints`; excluded rotary proxy intervals
may produce `rotary_proxy_sweep_clear_unverified_body` **only if
every rotationally changing segment is excluded** and no other
candidate contact is reported. More conservative legacy
chord/waypoint hazards retain priority. A positive result asserts
**only the supplied sphere/AABB and explicitly listed self-pair
checks** for *linear joint interpolation*. It does not clear real
controller trajectories, missing robot volumes/meshes, uncertain
terrain, contact forces, friction, unmodelled obstacles, sensor
errors or physical robot movement.

The output records the evaluation count, remaining unresolved
intervals, segment status and a fractional interpolation coordinate
for an observed collision. Neither a sampled overlap nor a clear
declared-proxy result is evidence of a completed physical experiment.
The separate validation task [#100](https://github.com/MatPomGit/arc-rvi/issues/100)
must independently challenge the analytic bound and near-contact
cases before #99 can be treated as a verified feasibility oracle.

The existing sampled collision and possible-chord statuses retain
priority when those findings are present. Continuous arbitrary
revolute joint motion, base motion, unlisted self-collisions, mesh
geometry, trajectory timing/dynamics, leg contacts, inverse kinematics,
slip and physical Unitree G1 EDU safety are **still not evaluated**.
The report retains `continuous_articulated_collision_validation:
not_performed`. This is a bounded preflight for P03 **candidate
rejection**, not authorization to move a robot.

Current implementation: deterministic planar greedy viewpoint baseline, mission
state guards, threshold decisions on supplied measurements, file hashing, paired fixture
benchmarking and a planar geometric simulator. The simulator has a separate observation
contract and never implements physical-device motion. See [the model](simulation.md).
Not implemented: perception, motion control, image feature extraction, real
camera capture, actual physics simulator integration and closed-loop operation.

The baseline hardware target for forthcoming simulation-model integration and
authorized physical validation is **Unitree G1 EDU**, as declared in
`config/robot.yaml`. Keep this designation in the
hardware configuration and experiment provenance, not hard-coded in planning,
perception or evaluation algorithms. Import and validate the exact delivered
variant's model, sensors, transforms, firmware and SDK before introducing a
device adapter. Current planar tests are generic and are not G1 dynamics tests.

External analytical models receive a neutral manifest and images; they do not
control motion and are not embedded into this research code.
