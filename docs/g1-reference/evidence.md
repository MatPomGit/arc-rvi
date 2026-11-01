# Evidence limits and ingestion risks

Version 1.0.0 | 2026-11-01 | No live connection, SDK compilation or physical test.

The 2026-04-14 log and the video are historical material. The log contains **299 logged Unitree TX entries**, **231 detection entries** and **197 logged zero transitions** for lost/invalid detections. These are counts of **logged entries**, not a census of every DDS/API packet or proof of physical motion. A separate calibration report dated 2026-04-17 lists 734 input video frames, 245 analyzed frames and 25 detections (10.2%); it has no independently labeled ground truth or verified synchronization with the log. The video is 1280×720, but one logged camera node reports 640×480.

Safety and integrity findings:

1. `robot_g1.py` creates a `rt/lowcmd` publisher, calls `ReleaseMode()` and transmits at a nominal 500 Hz; it cannot be treated as a read-only adapter.
2. `controller.py` can publish a 29-joint vector after receiving state for only one recognized joint; other values may remain at their initial zero positions.
3. `real_g1.py` does not validate incoming `JointState` timestamps, device variant or joint ranges at the hardware output.
4. `camera.py` maps MediaPipe poses to four joint targets without robot-specific kinematic validation.
5. `main.py` overwrites floating-base state in MuJoCo. It cannot validate physical balance or walking.
6. The Livox files use zero extrinsics and a shared `livox_frame`. No verified camera/robot/LiDAR TF2 chain, time synchronization or calibration exists in these materials.
7. The `g1.zip` example `terminations.cpp` accesses shared low-level state without explicit synchronization; it is not certified termination logic.
8. The supplied `control.yaml` and `bridge(1).yaml` have comments dated 19–20 April, **after** the April 14 log. They cannot establish that the E-STOP gateway was active during that recording.
9. SDK, Livox driver and ROS dependency versions, vendor commit hashes, source licenses and actual G1 firmware were not independently matched to these uploads.

**Use in ARC-RVI:** documentation of interfaces, synthetic offline parser fixtures, dropped/stale-message tests and exploratory failure taxonomies. Possible relevance: P02 perception, P06 image-quality gating and P07 data/clock-domain gap analysis. **Do not claim** confirmed real-world visual inspection, vehicle localization, robot stop performance, coverage, successful actuation or sim-to-real predictive validity.

Privacy and rights: leave raw videos, archives, telemetry and private host addresses outside public Git. Store only normalized descriptions and source hashes pending rights clearance. The physical adapter remains disabled (`adapter: not_configured`). Physical experiments require the independently reviewed [safety gates](../safety.md).

## Additional historical archives (2026-11-01)

Static audit of [`Old_program.zip` and `Program5.zip`](legacy-programs.md) and [RoboMVP 0.2.0](robomvp.md) adds software-level interfaces, not physically measured outcomes. **High-priority safety concerns:** the RoboMVP nominal demo initializes SDK despite `require_robot_connection=false`; its software E-STOP cannot establish hardware stop performance, and reset may attempt reconnection. The launch and main node both instantiate an odometry publisher, so `/odom` does not provide independent ground truth. The RoboMVP source also has a package-license mismatch (MIT package metadata versus Apache 2.0 license file). Old environment notes contain a device password and network details; neither is copied into this public repository. The new `Program5.zip` archive consists entirely of `.pyc` without source, so no behavioral claims can be made. Treat all of these as **unverified historical reference material**.

## Supplementary PDF source (2026-11-01)

[Robot hardware and operator summary](robot-info.md) is a secondary, non-revisioned PDF; it claims a 29-DOF model, RealSense D435i, Livox MID360 and four microphones, none independently verified as installed. Its stair-use and stick-calibration statements conflict internally; hip/knee/waist limits do not fully match source-code controller bounds. R3 shortcuts and motor-mode descriptions are **reference-only, not operating instructions**. Quadruped ROS Melodic examples are not a G1/ROS 2 implementation, and Unitree L1/L2 LiDAR tools are not the Livox MID360 driver. No physical motion, device inventory or additional research evidence is established.
