# G1 / ROS 2 / Livox: reference intake

Version: **1.0.0** | 2026-11-01 | **static reference, not deployed**.

This folder records commands, interfaces, parameters and provenance extracted from user-supplied Unitree G1 and Livox materials. It does **not** establish the actual G1 EDU variant, operating firmware, live topic graph, physical calibration, safety approval, or a working hardware adapter.

- [Commands and SDK interfaces](commands.md)
- [ROS 2, LiDAR and joint data](data-and-configuration.md)
- [Evidence and safety limitations](evidence.md)
- [Project data contract](../data-interface.md)
- [Physical test safety gates](../safety.md)

## Source archive identity

| Archive | Files | SHA-256 |
|---|---:|---|
| `g1.zip` | 15 | `cf6b91a1440b6784e071d60f252a9ff89a9c1c65cdc04667f92393e6d5b743cb` |
| `launch_ROS2.zip` | 5 | `eeef716d3162acbb0138268d2e87da5f29212236253c8d88943c9e86b1e13865` |
| `config.zip` | 5 | `fb932a185d4b3976637e8aec46be1e0498cd3efad2f2b7401ad43f1d07aa9121` |
| `Sterowanie_ROS2.zip` | 9 | `64886616b50e33d574977d6a985c061771b75904256bddd1e0dab33e04078d0e` |

The original archive content is **not** copied to the public repository: source licensing and revisions have not been authenticated. Private network IP addresses, local paths, recordings, raw telemetry and executable motion code are intentionally excluded. Hashes identify the user-supplied bytes, not a verified upstream commit.

Current ARC-RVI physical motion remains blocked: `config/robot.yaml` must retain `adapter: not_configured`. Treat all motion commands as reference text, never executable instructions for autonomous agents.
