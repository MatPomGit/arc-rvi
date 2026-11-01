# Historical G1 programs: source-derived interface reference

Version 1.0.0 | 2026-11-01 | Static archival examination only. No program executed.

## Archive inventory

| Source | SHA-256 | Usable evidence |
|---|---|---|
| `Program5.zip` | `b9e264a19512cc7cf838ad56128da48eb45924554490e3a884d27c295bd778ed` | 96 CPython 3.13 `.pyc` files; **zero Python source files** |
| `Old_program.zip` | `363d146c2f9f845c219cb4466cd6928a9f5c500efcc560546c34e2987f7e4442` | 13 Python source files, 13/13 static AST parse PASS; pretrained `.pt` and audio are **not** interpreted |

`Program5.zip` provides module **names only**, not trustworthy behavioral evidence. Its directory structure mentions `g1_light_tracking` (detector, follower, RealSense, arm skill bridge, light replay), `robot_emergency_stop` (E-STOP), and `robot_mission_control` (supervisor, health, ROS Action, ROS bag, UI). Bytecode was neither imported, disassembled nor run. No working E-STOP or mission behavior can be inferred.

## Old_program: functions and interfaces

| Source | Source-declared role | Access |
|---|---|---|
| `Program2/isaac.py` | subscribes `/joint_states`, publishes `/cmd_joint` (`sensor_msgs/JointState`); 0.005 s control timer; references a policy model | SIM publisher, **WRITE** if bridged to robot |
| `Program2/real_g1.py` | subscribes `/cmd_joint`; G1 SDK bridge | **WRITE**, hardware blocked |
| `Program2/robot_g1.py` | `RobotG1`, `rt/lowstate` subscriber and `rt/lowcmd` publisher | RO state / **WRITE** torque-position control |
| `Program5/sim_camera_ros.py` | MediaPipe 2D pose, `/cmd_joint` publisher | SIM only if isolated |
| `Program5/depth_camera_ros.py` | RealSense RGB/depth skeleton; filtering, loss-of-tracking and target mapping | SIM by default, may be provided with a hardware controller |
| `Program5/main.py` | ROS 2 camera/arm controller, `LowStateReader` on `rt/lowstate`, `ArmSdkController` on `rt/arm_sdk` | `robot-preflight` RO candidate; `robot` and `depth-robot` **WRITE** |
| `Program5/run_rl_velocity.sh` | builds and starts `unitree_rl_lab` `g1_ctrl` | **WRITE**, physically hazardous |
| `Program3/*`, `Program4/*`, `Program7/*` | audio, transfer, GUI, scripted sequences | separate demos; no autonomous inspection evidence |

`Program2/model_2999.pt` is an opaque, unverified PyTorch artifact; do **not** call `torch.load` on it, execute the policy or attribute training provenance. `Program3/sounds/Mielec.wav` is not a sensor measurement.

## CLI reference (historical, not execution instructions)

`Program5/main.py` modes: `--mode sim` (default), `--mode depth-sim`, `--mode robot-preflight`, `--mode robot`, `--mode depth-robot`. Physical modes are **BLOCKED**. The source requires `--i-understand-this-controls-real-robot` for physical modes and a separate explicit flag for hardware `--auto-start`; these are *software opt-ins*, not site authorization. The read-only-preflight path subscribes to `rt/lowstate` without constructing an `arm_sdk` writer, but it still requires authorized network access.

Notable source flags: `--max-joint-speed`, `--smoothing-hz`, `--depth-sample-radius`, `--calibration-frames`, `--require-hand-depth`, `--left-wrist-roll-sign`, `--depth-forward-sign`, `--shoulder-roll-gain`, `--arm-command-hz`, `--robot-tracking-loss-timeout`, `--robot-tracking-release-duration`, `--balance`, `--auto-start`. Values and guarantees are code-specific, not measured robot performance.

Selected defaults from the source: `width=640`, `height=480`, `fps=30`, `kp=30.0`, `kd=2.4`, `arm-command-hz=250`, `arm-stream-max-speed=7.0 rad/s`, `max-joint-speed=1.4 rad/s`, `robot-tracking-loss-timeout=0.45 s`, `robot-tracking-release-duration=0.6 s`. None is a verified safe hardware limit. `rt/arm_sdk` writes target positions and gains; do not equate software smoothing or a loss-of-tracking release with certified collision avoidance, balance or E-STOP.

## Security, licensing and reuse

Historical environment notes embed a plaintext device login/password and machine-specific network information. **Never copy, publish or rely on these credentials.** Replace any shared/default credential on the physical device according to its authorised administration procedure. The RoboMVP license is discussed separately in [its review](robomvp.md).

Relevance to ARC-RVI: offline parser fixtures for pose streams, simulated command-source isolation, camera-depth missingness, tracking dropout and actuator-latency *hypotheses*. They do not establish visual inspection, measured proprioception, physical safety or end-to-end vehicle photography. [Physical safety gate](../safety.md) remains authoritative.
