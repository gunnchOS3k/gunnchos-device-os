"""Dock manager — Gate 1 continuity-aware stub.

Physical dock success is never claimed here.
Status remains PHYSICAL_DOCK_EVIDENCE_PENDING until real evidence exists.
"""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.dock.continuity import DockContinuityEngine


def dock_state(connected: bool = False) -> dict:
    return {
        "docked": connected,
        "external_display": connected,
        "performance": "docked_performance" if connected else "balanced",
        "status_tokens": ["PHYSICAL_DOCK_EVIDENCE_PENDING"],
        "claim_boundary": "Stub state only; not physical dock evidence.",
    }


def continuity_engine(device_id: str | None = None) -> DockContinuityEngine:
    eng = DockContinuityEngine()
    if device_id:
        eng.device_id = device_id
    return eng


def simulate_dock_cycle(device_id: str | None = None) -> dict[str, Any]:
    from gunnchos_device_os.dock.simulator import run_dock_simulation

    return run_dock_simulation(device_id=device_id)
