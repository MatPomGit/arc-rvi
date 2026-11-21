# G1 / ROS 2 / Livox: reference intake

Version: **1.2.0** | 2026-11-01 | **static reference, not deployed**.

This folder records commands, interfaces, parameters and provenance extracted from user-supplied Unitree G1 and Livox materials. It does **not** establish the actual G1 EDU variant, operating firmware, live topic graph, physical calibration, safety approval, or a working hardware adapter.

- [Commands and SDK interfaces](commands.md)
- [ROS 2, LiDAR and joint data](data-and-configuration.md)
- [Evidence and safety limitations](evidence.md)
- [Historical programs and bytecode-only archive](legacy-programs.md)
- [RoboMVP interfaces and safety audit](robomvp.md)
- [G1 hardware and pilot reference PDF](robot-info.md)
- [Project data contract](../data-interface.md)
- [Physical test safety gates](../safety.md)

## Historical footage and camera calibration from G1 EDU

The project owner identifies [`MatPomGit/alf-luca`](https://github.com/MatPomGit/alf-luca)
as a **program actually run on a Unitree G1 EDU**. Unlike the static archived
SDK references below, this repository contains candidate historical image
and calibration material from that deployment:

| Source | Verified repository content | Interpretation |
|---|---|---|
| [`video/`](https://github.com/MatPomGit/alf-luca/tree/main/video) | Nine MP4/MKV recordings, including `kalibracja`, `sledzenie_plamki` and `apriltags_approach` | Candidate historical recordings; the repository alone does not establish per-file camera identity or unmodified acquisition |
| [`images_calib/`](https://github.com/MatPomGit/alf-luca/tree/main/images_calib) | 39 PNG chessboard-frame images | Selected/extracted calibration frames, **not** unmodified raw video; filenames and content hashes should be retained when imported |
| [`camera_calib.npz`](https://github.com/MatPomGit/alf-luca/blob/main/camera_calib.npz) | Calibration artifact in the repository root | Calibration candidate; its intrinsic parameters, reprojection error and device association need verification |
| [`tools/extract_calibration_images.py`](https://github.com/MatPomGit/alf-luca/blob/main/tools/extract_calibration_images.py) | Script selecting chessboard frames from MP4/MKV | Provides an inspectable extraction method, not proof of camera-model validity |

The G1 EDU execution history is **owner-confirmed**; the provenance of each
individual video, sensor serial, firmware version, extrinsic transforms and
capture clock have **not** been independently established. Source files stay
in `alf-luca`, not in ARC-RVI or its public documentation build. Reuse is
subject to image rights, calibration checks and session-level separation for
any evaluation dataset. This historical material does not demonstrate
physical ARC-RVI inspection, a functioning robot adapter or validated safety.

## Source archive identity

| Archive | Files | SHA-256 |
|---|---:|---|
| `g1.zip` | 15 | `cf6b91a1440b6784e071d60f252a9ff89a9c1c65cdc04667f92393e6d5b743cb` |
| `launch_ROS2.zip` | 5 | `eeef716d3162acbb0138268d2e87da5f29212236253c8d88943c9e86b1e13865` |
| `config.zip` | 5 | `fb932a185d4b3976637e8aec46be1e0498cd3efad2f2b7401ad43f1d07aa9121` |
| `Sterowanie_ROS2.zip` | 9 | `64886616b50e33d574977d6a985c061771b75904256bddd1e0dab33e04078d0e` |
| `Program5.zip` | 96 bytecode-only | `b9e264a19512cc7cf838ad56128da48eb45924554490e3a884d27c295bd778ed` |
| `Old_program.zip` | 23 | `363d146c2f9f845c219cb4466cd6928a9f5c500efcc560546c34e2987f7e4442` |
| `RoboMVP.zip` | 83 | `dfa76b5585e7da9dc4c94a3b2184b9153b5c01120fd1acae62c6bb32d601161c` |
| `Robot_info.pdf` | 6 pages | `755c70d099550df38745a74b4757f6b65ba36850d1c74023c88beebc7951c0a7` |

The original archive content is **not** copied to the public repository: source licensing and revisions have not been authenticated. Private network IP addresses, local paths, recordings, raw telemetry and executable motion code are intentionally excluded. Hashes identify the user-supplied bytes, not a verified upstream commit.

Current ARC-RVI physical motion remains blocked: `config/robot.yaml` must retain `adapter: not_configured`. Treat all motion commands as reference text, never executable instructions for autonomous agents.
