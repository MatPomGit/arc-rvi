# RoboMVP 0.2.0: ROS 2 interface and evidence audit

Version 1.0.0 | 2026-11-01 | Source: user-provided `RoboMVP.zip`, SHA-256 `dfa76b5585e7da9dc4c94a3b2184b9153b5c01120fd1acae62c6bb32d601161c`.

**Status:** 16 Python files, 16/16 static syntax parse PASS. No ROS 2 node, SDK, test, actuator, camera or network connection was executed. Project README claims Unitree G1 EDU; exact hardware identity not independently verified. Internal `.git` data, documents with embedded media and executable source are not copied into ARC-RVI.

## Claimed scenario, not independently verified execution

The source describes seven stages: find AprilTag table ID 21, detect box ID 10, align, pick, rotate 180 degrees, move toward table ID 22 / target ID 30, place. This is a fixed-waypoint manipulation demonstration, **not** an inspection or validated planner. `config/scene.yaml`: `stop_distance_threshold=0.3 m`, `alignment_threshold=0.05 m`; timeout parameters `search_table=20`, `detect_marker=20`, `align_with_box=10`, `navigate_to_target_marker=25`, `motion.total=30`, `motion.step=5` (seconds). These are source values, not physically validated thresholds.

## Topics from Python ROS 2 declarations

| Topic | Type | Direction / source | Access |
|---|---|---|---|
| `/camera/body/image_raw` | `sensor_msgs/Image` | `camera_interface` publishes | observation |
| `/camera/head/image_raw` | `sensor_msgs/Image` | `camera_interface` publishes | observation |
| `/robomvp/marker_detections` | `robomvp/MarkerDetection` | `marker_detection` publishes | observation |
| `/robomvp/marker_pose` | `robomvp/MarkerPose` | `marker_pose_estimator` publishes | estimated pose |
| `/robomvp/offset` | `robomvp/Offset` | `marker_pose_estimator` publishes | estimated correction |
| `/robomvp/state` | `robomvp/State` | `main_node` publishes | state |
| `/robomvp/motion_command` | `std_msgs/String` | `main_node` publishes | command intent, **not measured motion** |
| `/odom` | `nav_msgs/Odometry` | `robomvp_odometry` publishes | dead reckoning only |
| `/tf`, `/tf_static` | TF2 | `odometry` / `tf_publisher` | model transform, uncalibrated |
| `/diagnostics` | `diagnostic_msgs/DiagnosticArray` | `robomvp_diagnostics` | estimated health |
| `/cmd_vel` | `geometry_msgs/Twist` | teleop subscribes | **WRITE if teleop active and SDK available** |
| `/robomvp/teleop_active` | `std_msgs/Bool` | teleop publishes | status, not safety certification |

The launch file `demo.launch.py` starts eight node definitions: TF, camera, detection, pose, odometry, diagnostics, main, teleop. Default `marker_type=apriltag`, `require_robot_connection=false`, `teleop_enabled=false`, `step_period=1.0`, `body_camera_device=0`, `head_camera_device=-1`. The camera node publishes at 10 Hz, odometry 50 Hz, diagnostics 1 Hz. These are configured frequencies, not measured throughputs.

## Operator interfaces: behavior and hazards

| Endpoint | Type | Semantic role | Classification |
|---|---|---|---|
| `/robomvp/pause` | `std_srvs/SetBool` | pause scenario timer | operational; does **not** interrupt ongoing motion thread |
| `/robomvp/emergency_stop` | `std_srvs/Trigger` | call SDK disconnect, including StopMove/Damp | **software stop**, not verified independent E-STOP |
| `/robomvp/reset` | `std_srvs/Trigger` | recreate state machine, unpause, attempted SDK reconnection | **potential hardware side effect** |
| `/robomvp/manipulation_task` | `robomvp/ManipulationTask` Action | execute `full_scenario`, `approach_table`, `pick_box`, `rotate_180`, `walk_to_second_table`, `place_box` | **WRITE** if SDK available |

Action goal: `string sequence_name`, `bool apply_offset`. Result: `bool success`, `string message`, `float32 elapsed_seconds`, `string final_state`. Feedback: `int32 current_step`, `int32 total_steps`, `float32 progress`, `string step_description`, `string current_state`.

Message schemas: `MarkerDetection` contains `marker_id:int32`, `image_x:float32`, `image_y:float32`, `size:float32`; `MarkerPose` contains `marker_id`, metric `x,y,z` in *camera frame*, and quaternion `qx,qy,qz,qw`; `Offset` contains `dx,dy,dz:float32`; `State` contains `state_name:string` and `state_id:int32`.

## Calibration and inference limits

`config/camera.yaml` declares body 640×480 with intrinsics `fx=fy=600, cx=320, cy=240`, head 1280×720 with `fx=fy=900, cx=640, cy=360`; marker size `0.1 m`. These are supplied constants, **not an independently certified camera calibration**. The estimator uses apparent marker size and camera intrinsics to approximate range, and cannot independently verify true 6-DoF pose. `/odom` integrates **commanded** velocity; it is not measured robot odometry. Static TF offsets in the code are placeholders without surveyed extrinsics.

## Critical discrepancies, verified by static inspection

1. **Demo-mode is not isolation.** `main_node.py` calls `UnitreeRobotAPI.connect()` irrespective of `require_robot_connection`; the flag only decides whether a connection error is fatal. `connect` initialises SDK and invokes `Start()` to change operating mode. Even when teleop is disabled, `robomvp_teleop.py` invokes `_try_connect_sdk()`. Do not run the advertised demo on a robot network.
2. **Software stop is not fail-safe.** `pause` does not interrupt the motion thread; the `emergency_stop` service calls `disconnect` but returns success even if exceptions occur. There is no independent hardware-stop confirmation. `reset` contains an SDK reconnection path; `_robot_connected` state is not consistently cleared by E-STOP, so reconnection behavior is also inconsistent.
3. **Duplicate odometry.** `demo.launch.py` launches an `OdometryNode`, while `main_node.py` creates another instance in-process. Only the latter receives SDK velocity callbacks; publishing a separate `/odom` stream could produce conflicting/incomplete estimates.
4. **No physical reference truth.** Marker orientation in `MarkerPose` is documented as identity; camera calibration, odometry drift, real pose and successful grasp are not independently measured.
5. **License conflict.** `package.xml` declares MIT, while top-level `LICENSE` contains Apache License 2.0. Clarify attribution/rights before copying any RoboMVP source into ARC-RVI.

Read-only commands `ros2 topic list`, `ros2 topic info /robomvp/state`, `ros2 interface show robomvp/action/ManipulationTask` are **suggested inspection commands**, not proof those topics exist. The project's `./scripts/run_demo.sh`, `--robot`, ROS service/action calls and `/cmd_vel` can have hardware side effects: **do not execute them** as part of ARC-RVI ingestion.

## Scientific reuse

Potential: P02 marker/pose uncertainty and abstention, P03 state-machine feasibility, P05 commanded-versus-measured repeatability, P07 model mismatch. This is **source and interface evidence**, not a collected physical dataset and not grounds for real robot operation. Preserve `adapter: not_configured`, separate mock/simulation from hardware and follow [physical safety checks](../safety.md).
