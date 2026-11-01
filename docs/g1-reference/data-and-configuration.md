# G1, ROS 2 and Livox data reference

Version 1.0.0 | 2026-11-01 | Source-derived declarations, **not** an observed live ROS graph.

## Topics, message types and access

| Topic | Source-declared type | Role and boundary |
|---|---|---|
| `/cmd_joint` | `sensor_msgs/msg/JointState` | ROS joint command, **WRITE** when bridged to hardware |
| `/joint_states` | `sensor_msgs/msg/JointState` | simulated feedback from `main.py`; not physical telemetry |
| `/clock` | `rosgraph_msgs/msg/Clock` | MuJoCo simulation time, not UTC |
| `rt/lowstate` | Unitree `LowState_` | SDK2 feedback; read-only candidate |
| `rt/lowcmd` | Unitree `LowCmd_` | direct motor actuation, **WRITE** |
| `rt/secondary_imu` | Unitree `IMUState_` | torso IMU feedback (example only) |
| `rt/arm_sdk` | Unitree `LowCmd_` | upper-limb actuation, **WRITE** |
| `rt/lf/dex3/{left,right}/state` | Unitree `HandState_` | hand state |
| `rt/dex3/{left,right}/cmd` | Unitree `HandCmd_` | hand actuation, **WRITE** |
| `rt/audio_msg` | Unitree DDS `String_` | audio/ASR event |
| `/livox/lidar` | `PointCloud2` in RViz profile | reference display topic; requires driver validation |
| `/camera/image_raw`, `/light_tracking/detection_json` | no schema provided | historical camera/detector input and output |
| `/cmd_vel_raw`, `/cmd_vel`, `/api/sport/{request,response}` | no message schema provided | historical motion pipeline; **WRITE** to robot |
| `/emergency_stop/active` | `Bool` per YAML comment | proposed signal; physical effectiveness not established |

## Livox launch files and profiles

| Launch | Sensor | `xfer_format` | RViz | JSON profile |
|---|---|---:|---|---|
| `msg_HAP_launch.py` | HAP | 1, custom message | no | `HAP_config.json` |
| `msg_MID360_launch.py` | MID360 | 1, custom message | no | `MID360_config.json` |
| `rviz_HAP_launch.py` | HAP | 0, PointCloud2 | yes | `HAP_config.json` |
| `rviz_MID360_launch.py` | MID360 | 0, PointCloud2 | yes | `MID360_config.json` |
| `rviz_mixed.py` | HAP + MID360 | 0, PointCloud2 | yes | `mixed_HAP_MID360_config.json` |

Each launch declares `publish_freq=10.0`, `multi_topic=0`, `data_src=0`, `output_data_type=0`, `frame_id=livox_frame` and the `livox_ros_driver2_node` executable. `display_point_cloud_ROS2.rviz` selects `Fixed Frame=livox_frame`, topic `/livox/lidar`. The archives have the JSON settings but not the external driver. Device command, push-message, point-cloud, IMU and log ports are configurable in the JSON files; reference values for HAP are 56000/0/57000/58000/59000, and for MID360 56100/56200/56300/56400/56500 (device side). Host-side ports can differ, particularly for MID360. Raw private IP addresses are deliberately omitted. All provided extrinsic values (roll/pitch/yaw/x/y/z) are zero **placeholders**, not measured transforms.

## 29 joint indices from the Python bridge

The map comes from `robot_g1.py:G1JointIndex` and `real_g1.py:JOINT_MAP`. Indices are example offsets, **not** confirmed for the actual EDU variant.

| Indices | Names |
|---|---|
| 0–5 | left_hip_pitch, left_hip_roll, left_hip_yaw, left_knee, left_ankle_pitch, left_ankle_roll |
| 6–11 | right_hip_pitch, right_hip_roll, right_hip_yaw, right_knee, right_ankle_pitch, right_ankle_roll |
| 12–14 | waist_yaw, waist_roll, waist_pitch |
| 15–21 | left_shoulder_pitch, left_shoulder_roll, left_shoulder_yaw, left_elbow, left_wrist_roll, left_wrist_pitch, left_wrist_yaw |
| 22–28 | right_shoulder_pitch, right_shoulder_roll, right_shoulder_yaw, right_elbow, right_wrist_roll, right_wrist_pitch, right_wrist_yaw |

All names in this table carry the source suffix `_joint`. The `controller.py` source has 29 Polish aliases, five body-part groups, and 29 local min/max radian intervals. It also sets `JOINT_STEP_SPEED=2.4 rad/s`, FAST ×3 and FINE ×0.25; `camera.py` sets up to 1.2 rad/s for four arm joints. These source constants are **not verified motor safety limits**.

## Proposed neutral import contract

For offline parsing retain `session_id`, source SHA-256, original timestamp and clock domain, topic, message type, native units, `frame_id`, version and calibration hash, missingness reason and device/rights status. Unknown topic schemas, missing transforms and unconfirmed hardware identity must be rejected or marked `unverified`, never inferred from example paths. Keep simulation, source-code references and recorded physical observations distinct, and keep evaluation truth separate from controller inputs. No ROS 2 or DDS bridge is enabled by this document.


## Extracted numeric joint limits from controller.py

The values below are **software constants in the supplied example**. They are not verified physical safe ranges or an authorization to actuate.

| SDK index | Joint | Min (rad) | Max (rad) |
|---:|---|---:|---:|
| 0 | left_hip_pitch_joint | -2.5307 | 2.8798 |
| 1 | left_hip_roll_joint | -0.5236 | 2.9671 |
| 2 | left_hip_yaw_joint | -2.7576 | 2.7576 |
| 3 | left_knee_joint | -0.087267 | 2.8798 |
| 4 | left_ankle_pitch_joint | -0.87267 | 0.5236 |
| 5 | left_ankle_roll_joint | -0.2618 | 0.2618 |
| 6 | right_hip_pitch_joint | -2.5307 | 2.8798 |
| 7 | right_hip_roll_joint | -2.9671 | 0.5236 |
| 8 | right_hip_yaw_joint | -2.7576 | 2.7576 |
| 9 | right_knee_joint | -0.087267 | 2.8798 |
| 10 | right_ankle_pitch_joint | -0.87267 | 0.5236 |
| 11 | right_ankle_roll_joint | -0.2618 | 0.2618 |
| 12 | waist_yaw_joint | -2.618 | 2.618 |
| 13 | waist_roll_joint | -0.52 | 0.52 |
| 14 | waist_pitch_joint | -0.52 | 0.52 |
| 15 | left_shoulder_pitch_joint | -3.0892 | 2.6704 |
| 16 | left_shoulder_roll_joint | -1.5882 | 2.2515 |
| 17 | left_shoulder_yaw_joint | -2.618 | 2.618 |
| 18 | left_elbow_joint | -1.0472 | 2.0944 |
| 19 | left_wrist_roll_joint | -1.9722 | 1.9722 |
| 20 | left_wrist_pitch_joint | -1.6144 | 1.6144 |
| 21 | left_wrist_yaw_joint | -1.6144 | 1.6144 |
| 22 | right_shoulder_pitch_joint | -3.0892 | 2.6704 |
| 23 | right_shoulder_roll_joint | -2.2515 | 1.5882 |
| 24 | right_shoulder_yaw_joint | -2.618 | 2.618 |
| 25 | right_elbow_joint | -1.0472 | 2.0944 |
| 26 | right_wrist_roll_joint | -1.9722 | 1.9722 |
| 27 | right_wrist_pitch_joint | -1.6144 | 1.6144 |
| 28 | right_wrist_yaw_joint | -1.6144 | 1.6144 |

The supplied SDK wrapper uses motor position gains `Kp=[60,60,60,100,40,40,60,60,60,100,40,40,60,40,40,40×14]` and velocity gains `Kd=[1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1×14]`, in the indicated SDK index order. These are reference code values only, not approved tuning.

## Reference Livox ports (private IP addresses removed)

| Sensor / profile | Channel | Device port | Host port |
|---|---|---:|---:|
| HAP | command | 56000 | 56000 |
| HAP | push | 0 | 0 |
| HAP | points | 57000 | 57000 |
| HAP | IMU | 58000 | 58000 |
| HAP | log | 59000 | 59000 |
| MID360 | command | 56100 | 56101 |
| MID360 | push | 56200 | 56201 |
| MID360 | points | 56300 | 56301 |
| MID360 | IMU | 56400 | 56401 |
| MID360 | log | 56500 | 56501 |

The mixed profile repeats these port assignments for both sensors. Port numbers are settings found in the provided JSON, **not** a measured physical network inventory.
