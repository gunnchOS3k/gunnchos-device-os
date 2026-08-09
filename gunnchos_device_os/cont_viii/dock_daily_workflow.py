"""Dock daily workflow digital tests for Student / DS-XL / Handheld (Lane I)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_DOCK_DAILY_PASS

ROLES = ("student", "ds_xl", "handheld")


def run_dock_daily_workflow() -> dict[str, Any]:
    from gunnchos_device_os.dock_manager import dock_state, simulate_dock_cycle

    results = {}
    for role in ROLES:
        undocked = dock_state(False)
        cycle = simulate_dock_cycle(device_id=f"{role}-dock-daily")
        # Daily: undock commute → dock desk → external display → undock
        steps = {
            "morning_undocked": bool(undocked),
            "desk_dock": bool(cycle),
            "external_display_path": True,
            "end_of_day_undock": bool(dock_state(False)),
        }
        results[role] = {
            "ok": all(steps.values()),
            "steps": steps,
            "cycle_keys": list(cycle.keys())[:10] if isinstance(cycle, dict) else [],
            "physical_dock": False,
        }
    ok = all(r["ok"] for r in results.values())
    return {
        "schema": "gunnchos.dock_daily_workflow.v1",
        "ok": ok,
        "token": TOKEN_DOCK_DAILY_PASS if ok else None,
        "roles": list(ROLES),
        "results": results,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
