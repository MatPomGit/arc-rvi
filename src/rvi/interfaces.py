"""Boundary contracts for future real/simulated devices."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class RobotAdapter(Protocol):
    def confirm_target(self, target_identifier: str) -> bool: ...
    def navigate_to(self, x: float, y: float) -> None: ...
    def capture_image(self, output_path: Path) -> None: ...
    def stop_motion(self) -> None: ...


class AdapterUnavailable(RuntimeError):
    """No authorized device or simulator adapter has been connected."""


# Simulation observations are separate from the physical-device contract.


@dataclass(frozen=True)
class CameraPose:
    x: float
    y: float
    yaw_rad: float


@dataclass(frozen=True)
class SimulatedObservation:
    pose: CameraPose
    visible_patch_ids: tuple[str, ...]
    elapsed_time_s: float
    travel_distance_m: float
    failure_reason: str | None


@runtime_checkable
class SimulatorAdapter(Protocol):
    def reset(self) -> None: ...
    def acquire(self, pose: CameraPose) -> SimulatedObservation: ...
