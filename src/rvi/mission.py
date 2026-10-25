"""High-level inspection state transitions; no actuator access here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MissionState(str, Enum):
    CREATED = "created"
    TARGET_CONFIRMED = "target_confirmed"
    PLANNED = "planned"
    ACQUIRING = "acquiring"
    QUALITY_CHECKED = "quality_checked"
    COMPLETE = "complete"
    ABORTED = "aborted"


_ALLOWED: dict[MissionState, frozenset[MissionState]] = {
    MissionState.CREATED: frozenset({MissionState.TARGET_CONFIRMED, MissionState.ABORTED}),
    MissionState.TARGET_CONFIRMED: frozenset({MissionState.PLANNED, MissionState.ABORTED}),
    MissionState.PLANNED: frozenset({MissionState.ACQUIRING, MissionState.ABORTED}),
    MissionState.ACQUIRING: frozenset({MissionState.QUALITY_CHECKED, MissionState.ABORTED}),
    MissionState.QUALITY_CHECKED: frozenset(
        {MissionState.ACQUIRING, MissionState.COMPLETE, MissionState.ABORTED}
    ),
    MissionState.COMPLETE: frozenset(),
    MissionState.ABORTED: frozenset(),
}


@dataclass
class Mission:
    state: MissionState = MissionState.CREATED

    def advance(self, target: MissionState) -> None:
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"invalid transition {self.state.value} -> {target.value}")
        self.state = target
