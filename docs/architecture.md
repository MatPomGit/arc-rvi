# Architecture

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
