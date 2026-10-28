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
    RETURNING = "returning"
    RETURN_VERIFIED = "return_verified"
    HANDOFF_CONFIRMED = "handoff_confirmed"
    COMPLETE = "complete"
    ABORTED = "aborted"


_ALLOWED: dict[MissionState, frozenset[MissionState]] = {
    MissionState.CREATED: frozenset({MissionState.TARGET_CONFIRMED, MissionState.ABORTED}),
    MissionState.TARGET_CONFIRMED: frozenset({MissionState.PLANNED, MissionState.ABORTED}),
    MissionState.PLANNED: frozenset({MissionState.ACQUIRING, MissionState.ABORTED}),
    MissionState.ACQUIRING: frozenset({MissionState.QUALITY_CHECKED, MissionState.ABORTED}),
    MissionState.QUALITY_CHECKED: frozenset(
        {MissionState.ACQUIRING, MissionState.RETURNING, MissionState.ABORTED}
    ),
    MissionState.RETURNING: frozenset({MissionState.RETURN_VERIFIED, MissionState.ABORTED}),
    MissionState.RETURN_VERIFIED: frozenset({MissionState.HANDOFF_CONFIRMED, MissionState.ABORTED}),
    MissionState.HANDOFF_CONFIRMED: frozenset({MissionState.COMPLETE, MissionState.ABORTED}),
    MissionState.COMPLETE: frozenset(),
    MissionState.ABORTED: frozenset(),
}


@dataclass
class Mission:
    state: MissionState = MissionState.CREATED
    handoff_anchor_id: str | None = None

    def advance(self, target: MissionState, *, evidence: dict | None = None) -> None:
        """State-only guard; supplied evidence is not a physical safety authorization."""
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"invalid transition {self.state.value} -> {target.value}")
        if target == MissionState.RETURNING:
            if (not isinstance(evidence, dict)
                    or evidence.get("all_required_slots_accepted") is not True
                    or evidence.get("independent_qc_complete") is not True):
                raise ValueError("cannot leave acquisition without accepted independent QC")
        if target == MissionState.RETURN_VERIFIED:
            if (not isinstance(self.handoff_anchor_id, str) or not self.handoff_anchor_id.strip()
                    or not isinstance(evidence, dict)
                    or evidence.get("anchor_id") != self.handoff_anchor_id
                    or evidence.get("status") != "arrived"
                    or evidence.get("safe_route_verified") is not True):
                raise ValueError("safe return to original handoff anchor not verified")
        if target == MissionState.HANDOFF_CONFIRMED:
            if (not isinstance(evidence, dict)
                    or evidence.get("anchor_id") != self.handoff_anchor_id
                    or evidence.get("operator_handoff_confirmed") is not True):
                raise ValueError("operator handoff not confirmed")
        self.state = target
