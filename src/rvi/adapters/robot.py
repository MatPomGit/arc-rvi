"""Hardware integration deliberately unavailable until explicitly validated."""

from pathlib import Path

from ..interfaces import AdapterUnavailable


class UnconfiguredRobotAdapter:
    def confirm_target(self, target_identifier: str) -> bool:
        raise AdapterUnavailable("robot target identification not configured")

    def navigate_to(self, x: float, y: float) -> None:
        raise AdapterUnavailable("robot motion not configured")

    def capture_image(self, output_path: Path) -> None:
        raise AdapterUnavailable("robot camera not configured")

    def stop_motion(self) -> None:
        raise AdapterUnavailable("robot safety stop not configured")
