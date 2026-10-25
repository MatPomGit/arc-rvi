"""Boundary contracts for future real/simulated devices."""

from __future__ import annotations

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
