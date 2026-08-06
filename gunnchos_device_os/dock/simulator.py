"""Software dock continuity simulator."""
from __future__ import annotations

from typing import Any

from .continuity import DockContinuityEngine

STATUS_SIM_PASS = "DOCK_CONTINUITY_SIMULATION_PASS"
STATUS_PHYSICAL_PENDING = "PHYSICAL_DOCK_EVIDENCE_PENDING"


def run_dock_simulation(
    *,
    device_id: str | None = None,
    dock_id: str = "sim-dock-001",
    interrupt: bool = True,
) -> dict[str, Any]:
    engine = DockContinuityEngine()
    if device_id:
        engine.device_id = device_id

    engine.save_blob = {"slot": 1, "progress": 42, "chapter": "intro"}
    engine.apps = ["launcher", "campus-notes", "media"]

    attach = engine.attach(dock_id, external_display=True, ethernet=True)
    # Route / peripheral detection already captured in attach event
    engine.enter_degraded_mode("transient_link_glitch")
    engine.restore_from_snapshot()
    # Re-attach cleanly after restore of prior docked snapshot
    if not engine.docked:
        engine.attach(dock_id)
    undock = engine.safe_undock()
    if interrupt:
        # Simulate mid-session interruption recovery while undocked
        engine.snapshot_session()
        engine.apps = ["corrupted-temp"]
        engine.recover_interruption()

    report = engine.continuity_report()
    continuity_ok = (
        not engine.errors
        and undock.get("safe") is True
        and attach.get("kind") == "attach"
        and engine.save_blob.get("progress") == 42
    )
    status = [STATUS_SIM_PASS if continuity_ok else "DOCK_CONTINUITY_SIMULATION_FAIL"]
    status.append(STATUS_PHYSICAL_PENDING)

    return {
        "schema": "gunnchos.dock_evidence.v1",
        "simulation": True,
        "physical_dock": False,
        "continuity_ok": continuity_ok,
        "status_tokens": status,
        "report": report,
        "claim_boundary": (
            "DOCK_CONTINUITY_SIMULATION_PASS is software-only. "
            "PHYSICAL_DOCK_EVIDENCE_PENDING until real-device evidence is attached."
        ),
    }
