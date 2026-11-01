# G1 commands and SDK reference

Version 1.0.0 | 2026-11-01 | User-provided sources; **not executed**.

**RO:** observation only. **SIM:** isolated simulation only. **WRITE:** actuates hardware, changes control modes or writes to a device; blocked in ARC-RVI. **ENV:** historical installation information, unverified for the local platform.

## Python ROS 2 interface

| Source | Node / access | Subscribed input | Published output |
|---|---|---|---|
| `main.py` | `robot_g1_sim`, SIM | `/cmd_joint` (`JointState`) | `/joint_states` (`JointState`), `/clock` (`Clock`) |
| `controller.py` | `g1_manual_controller`, SIM or WRITE | `/joint_states` | `/cmd_joint` (`JointState`) |
| `camera.py` | `camera_mediapipe_controller`, SIM or WRITE | local V4L2 camera | `/cmd_joint` (`JointState`) |
| `real_g1.py` | `g1_ros_bridge`, **WRITE** | `/cmd_joint` | SDK2 `rt/lowcmd` (`LowCmd_`) |
| `robot_g1.py` | SDK2 wrapper, **WRITE** | `rt/lowstate` (`LowState_`) | `rt/lowcmd` (`LowCmd_`) |

Source command sequence (the original machine-specific path is intentionally abstracted):

```bash
# SIM only, against an isolated MuJoCo instance without a robot DDS bridge
source ~/ros2_humble/install/setup.bash
source ~/RobotG1/unitree_mujoco/venv/bin/activate
python <PROGRAM1>/main.py
python <PROGRAM1>/controller.py
python <PROGRAM1>/camera.py
```

These are *quoted historical commands*, not verified installation instructions. `main.py` expects a machine-specific MuJoCo `scene.xml`, implements PD gains Kp=60/Kd=3, publishes a simulation clock, and explicitly constrains floating-base motion. Never count its motion as valid humanoid dynamics. `controller.py` uses Pygame and publishes all 29 joint commands; `camera.py` converts MediaPipe pose landmarks to commands for four arm joints. These publishers can conflict if started concurrently.

The source also contains `python <PROGRAM1>/real_g1.py`. This is a **WRITE operation: do not execute**. It initializes a hardware SDK publisher and a periodic `LowCmd_` writer (nominal 500 Hz), and calls `MotionSwitcherClient.ReleaseMode()`. No independently verified E-STOP, watchdog, motor-limit enforcement or safe shutdown is supplied.

## C++ SDK2 methods extracted from `g1.zip`

| Source | Observation / query | State-changing operation, blocked |
|---|---|---|
| `high_level/g1_loco_client_example.cpp` | `GetFsmId`, `GetFsmMode`, `GetBalanceMode`, `GetSwingHeight`, `GetStandHeight`, `GetPhase` | `Move`, `SetVelocity`, `Start`, `StopMove`, `Damp`, `Squat`, `Sit`, `StandUp`, `ZeroTorque`, `HighStand`, `LowStand`, `BalanceStand`, `SetFsmId`, `SetBalanceMode`, `SetSwingHeight`, `SetStandHeight`, `ContinuousGait`, `SwitchMoveMode`, `SetTaskId`, `ShakeHand`, `WaveHand`, `SetSpeedMode` |
| `high_level/g1_arm_action_example.cpp` | `GetActionList` (`--list`, `--id 0`) | `ExecuteAction(id|name)` (`--id`, `--name`), `StopCustomAction` |
| `agv/g1_agv_client_example.cpp` | none in sample | `Move`, `HeightAdjust` |
| `audio/g1_audio_client_example.cpp` | `GetVolume`, subscription to `rt/audio_msg` | `SetVolume`, `TtsMaker`, `PlayStream`, `PlayStop`, `LedControl` |
| `high_level/g1_arm{5,7}_sdk_dds_example.cpp` | `rt/lowstate` subscription | publish `LowCmd_` on `rt/arm_sdk` |
| `dex3/g1_dex3_example.cpp` | `rt/lf/dex3/{left,right}/state` | `rt/dex3/{left,right}/cmd` (`HandCmd_`) |
| `low_level/g1_{ankle_swing,dual_arm}_example.cpp` | `rt/lowstate`, torso `rt/secondary_imu` | `rt/lowcmd`, `ReleaseMode` |
| `low_level/terminations.cpp` | `rt/lowstate` | no actuator write in this file |

The arm example says action execution needs FSM ID 500, 501 or 801 (with additional mode restrictions for 801). This is **not** proof that the supplied physical robot supports those modes. `CheckMode` is a query; `ReleaseMode` changes the active controller.

## Environment commands present in source

The historical setup notes mention `vcs import` for ROS 2 Humble, `rosdep install`, `colcon build --symlink-install --executor sequential`, `ros2 run demo_nodes_cpp talker`, `ros2 run demo_nodes_py listener`, Git clones of `unitree_mujoco`, `unitree_sdk2`, `unitree_sdk2_python`, and `unitree_ros2`, followed by package installation. Their dependency graph, license versions and system package commands were **not verified**. The SDK note mixes `ros-foxy-*` packages with Humble. Do not reuse its `sudo`, `curl` or cleanup commands in an agent without a fresh review.

## Historical locomotion bridge

In the 2026-04-14 log: `light_spot_detector_node` → `g1_light_follower_node` → `unitree_cmd_vel_bridge_node` → `/api/sport/request`. The later supplied YAML sets `control_rate_hz=20`, `linear_no_depth_speed=0.35`, `cmd_timeout_s=0.5`, `publish_rate_hz=10`, `max_vyaw=0.8`, `velocity_duration_s=0.2`. It references `/cmd_vel_raw`, `/cmd_vel` and `/emergency_stop/active`, but contains changes dated 19–20 April, after the log. The April 14 E-STOP behavior remains **unverified**.
