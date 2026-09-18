"""Continuity provider contract (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ContinuityState:
    session_id: str
    anchors: List[str] = field(
        default_factory=lambda: ["display", "input", "audio", "network", "app_context"]
    )
    tier: str = "digital_sim"
    dock_present: bool = False

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "anchors": self.anchors,
            "tier": self.tier,
            "dock_present": self.dock_present,
            "claim_boundary": "digital_sim_not_physical_dock_pass",
        }


def create_continuity_state(session_id: str) -> ContinuityState:
    return ContinuityState(session_id=session_id)
