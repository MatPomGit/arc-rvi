# Unitree G1: hardware, operator and software source notes

Version: **1.0.0** | Intake date: 2026-11-01 | Source class: **user-supplied secondary technical summary, unverified**.

**Source:** `Robot_info.pdf`, *Analiza robota Unitree G1 i oprogramowania*, 6 pages; SHA-256: `755c70d099550df38745a74b4757f6b65ba36850d1c74023c88beebc7951c0a7`. File is not committed, reproduced or distributed here. No publisher, exact manufacturer document revision, date or per-claim primary citation is supplied. The following retains the PDF's terminology and page numbers. **A source assertion is not a verified physical measurement or confirmation of the installed G1 EDU payload.**

## Source claims: mechanical platform (pp. 1-2)

| Property | Value reported in PDF | Verification state |
|---|---|---|
| G1 configuration | 29 actuated DOF | Source claim; agrees in *count* with the 29-index sample SDK map, but not necessarily the actual variant |
| Mass | >35 kg | No mass measurement, variant or payload |
| Maximum knee torque | 90 N m | No actuator identification or operating condition |
| Arm payload | up to 2 kg | No posture, speed, reach or operating-cycle qualification |
| Waist Z/yaw range | ±155° | Not interchangeable with per-axis software joint-limit table |
| Knee range | 0° to 165° | Conflicts in lower bound with historical example controller limits |
| Hip pitch | ±154° | Conflicts with asymmetric example-controller limits |
| Hip roll | -30° to 170° | Not independently cross-checked against actual assembled G1 |
| Hip yaw | ±158° | No physical validation |
| Encoders | dual encoders at each joint | Model-/revision-specific manufacturer evidence missing |

The historical code-derived limits and index names remain in [joint data](data-and-configuration.md). **Do not overwrite SDK limits or safety constraints from the PDF.** The PDF does not identify the precise delivered EDU option, motor SKUs or firmware.

## Claimed sensor payload (p. 2)

| Sensor | PDF description | Applicability gate |
|---|---|---|
| RGB-D camera | Intel RealSense D435i; depth range up to 3 m; FOV 87° horizontal × 58° vertical | No physical inventory, camera serial, frame rate, actual intrinsics, extrinsics or calibration |
| LiDAR 3D | Livox MID360, 360° horizontal scan | Distinguish from the separate HAP and MID360 *example* launch profiles; no device discovery, TF or clock sync |
| Microphone array | four microphones, sound detection and direction-of-arrival | No actual model, channel mapping, sample rate, array geometry or measured DOA performance |

The PDF reports these as present, but the [data contract](../data-interface.md) correctly treats the installed sensor payload, topics and transforms as **not verified**. A driver configuration or source description does not establish that any device is installed or operational. Example `/camera/*`, `/livox/lidar` or other topics are not operational defaults.

## R3 remote control: source reference (pp. 2-4)

PDF specifications: nominal USB charging voltage 5 V, charging current 700 mA, battery capacity 780 mAh, runtime 5 h and open-area radio range >100 m; connection described as digital data link and Bluetooth, with Unitree Explore App pairing. These are *unverified device-variant claims*, not qualified acceptance parameters. The same PDF recommends a USB-C 5 V/2 A supply (p. 3), which describes a supply capability rather than a confirmed actual charge current.

The source says: power on/off = short press then hold (>2 s); left stick = forward/backward; right stick = yaw left/right. It lists SELECT, START, L1/L2, R1/R2, F1/F3 and power. It separately instructs **F1 + F3, move sticks, then F5** to calibrate (p. 3), but F5 is absent from the enumerated controls. **Mark this sequence unresolved; do not perform from this document.**

Historical button combinations *as printed* (p. 3-4), recorded solely for source traceability:

| Function described | PDF combination |
|---|---|
| Debug | L2 + R2 |
| Zero Torque | Hold L2 + Y |
| Damping | Hold L2 + B |
| Standing lock | Hold L2 + D-pad up |
| Sitting | Hold L2 + D-pad left |
| Lying / rising | Hold L2 + X |
| Squat | Hold L2 + A |
| Wave hand | Hold SELECT + Y |
| Handshake | Hold SELECT + A |
| Rotate and wave | Hold SELECT + X |
| Slow / fast speed | R2 + D-pad down / R2 + D-pad up |
| Lean forward / back | Hold START + D-pad up / down |

**Safety classification:** every mode-switch, posture, gait or interaction shortcut is a potential **physical actuation or safety-state change**, not a read-only command. They are **BLOCKED for autonomous execution**. Validate against the exact manufacturer's manual, firmware and the human operator's on-site procedure before any authorised use. The PDF's descriptions of `Zero Torque` and `Damping` are informal; do not treat a particular mode as a reliable physical E-STOP or fall-arrest method.

## Grippers and mechanical servicing (pp. 4-5)

The PDF distinguishes a prosthetic hand for Basic/Standard/Advanced/Flagship variants from a three-finger `Dex3-1` for a Flagship variant. It reports clamp/panel screws in sizes M2/M3 and, for Dex3-1 harness clips, M3/M4/M6. The described Dex3-1 path includes separate power and signal harness connections; warns about cable routing near the heatsink/fan; and advises **against squatting or lying with Dex3-1 fitted**.

These statements are an **inventory and service-risk checklist**, not a verified installation procedure. No actual end-effector variant, cable route, connector pinout or maintenance authorization has been established. Do not publish or automatically follow screw-removal steps for a physical G1. Physical inspection should first identify the installed hand, support arrangement and manufacturer service instructions.

## Source-listed development ecosystem (pp. 5-6)

| Named resource | Role as described by PDF | Boundary for ARC-RVI |
|---|---|---|
| `unitree_sdk2` | C++ control and telemetry; source lists Ubuntu 20.04, GCC 9.4, CMake >=3.10, Eigen/Boost/spdlog | Version/dependency constraints may be outdated; pin exact supported upstream revision |
| `unitree_sdk2_python` | Python SDK; lists Python >=3.8, `cyclonedds`, `numpy`, `opencv-python`; both read and write | Separate read-only subscriptions from SDK publishers and RPCs that change state |
| `unitree_guide`, `unitree_ros`, `unitree_legged_msgs` | ROS/Gazebo educational examples, Ubuntu 18.04 and ROS Melodic | **Quadruped teaching examples are not a G1 ROS 2 adapter**; no inference of G1 locomotion validity |
| `unilidar_sdk`, `unilidar_sdk2` | Unitree L1/L2 LiDAR access | **Not** interchangeable with Livox MID360 driver or its messages |
| `point_lio_unilidar` | L1-oriented point-cloud/IMU SLAM | No G1-EDU/MID360 calibration or tested pipeline established |

The PDF describes a BSD-3-Clause open-source ecosystem, but **does not provide exact per-repository license files or commit hashes**. Do not extend this claim to all examples, ROS packages, drivers, documentation, binary models or copied code; license each upstream source independently.

## Inconsistencies and required verification

1. **Terrain contradiction:** p. 2 describes remote control on flat ground, inclines *and stairs*, while p. 6 says the *default gait cannot climb stairs*. Preserve both statements; do not assert stair-climbing availability or safety without validating the installed control policy.
2. **F5 omission:** the stick-calibration instructions reference F5, omitted from the button inventory (p. 3).
3. **Joint-limit conflict:** waist, knee and hip ranges do not exactly match the source-code limits documented in [ROS 2 joint data](data-and-configuration.md). This may reflect variants, conventions, revisions or source error; no reconciliation is possible from the supplied material alone.
4. **Variant/payload ambiguity:** the document mixes general G1, G1 Education, Flagship and different hand types without a serial-numbered bill of materials.
5. **Software mismatch:** ROS Melodic quadruped examples and Unitree L1/L2 LiDAR packages do not demonstrate support for the supplied G1 + Livox MID360 / ROS 2 setup.
6. **Unverified performance/operations:** weight, payload, torque, depth range/FOV, radio range/runtime, slope capability and standing/zero-torque mode effects lack independent test evidence.
7. **No primary provenance:** PDF has no authoritative source revisions, calibration receipts, experimental results, manufacturer safety certificates or evidence of physical installation.

### Intended scientific reuse

Use as a **secondary equipment specification candidate** for M0 device inventory, M1 interface/schema audit and M2 read-only sensor preflight, plus hypothesis generation for P02/P03/P07. Freeze actual variant, installed payload, source versions, camera/LiDAR TF2 transforms, clock domains, site approval and verified emergency-stop hardware before any physical study. This PDF does **not** change the project status from hardware-unverified, and does **not** unblock any actuator operation. Preserve `config/robot.yaml: adapter: not_configured`. See [physical safety](../safety.md) and [evidence limitations](evidence.md).
