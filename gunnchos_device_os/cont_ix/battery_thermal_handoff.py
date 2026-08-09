"""Battery/thermal physical handoff models + EVT procedures. Actual values PHYSICAL."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_BATTERY_THERMAL
from gunnchos_device_os.cont_viii.performance_models import MODELS, estimate_battery_hours


EVT_PROCEDURES = [
    {
        "id": "EVT-BAT-001",
        "title": "Battery discharge curve at room ambient",
        "status": "PHYSICAL_PENDING",
        "instrumentation": ["power_monitor", "thermocouple"],
    },
    {
        "id": "EVT-THM-001",
        "title": "SoC surface temperature under office + game load",
        "status": "PHYSICAL_PENDING",
        "instrumentation": ["IR_camera", "thermocouple"],
    },
    {
        "id": "EVT-THM-002",
        "title": "Docked thermal with external display active",
        "status": "PHYSICAL_PENDING",
        "instrumentation": ["thermocouple"],
    },
]


def evaluate_battery_thermal_handoff() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    models = []
    for m in MODELS:
        models.append(
            {
                "sku": m.sku,
                "battery_wh_model": m.battery_wh,
                "idle_w": m.idle_w,
                "active_w": m.active_w,
                "display_w": m.display_w,
                "battery_hours_model": estimate_battery_hours(m),
                "thermal_envelope_c_model": {"idle": 35.0, "active_warn": 70.0, "shutdown": 90.0},
                "actual_values": "PHYSICAL",
            }
        )

    # Write EVT procedure doc
    doc = root / "docs" / "release" / "EVT_BATTERY_THERMAL_PROCEDURES.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# EVT battery / thermal procedures",
        "",
        "PHYSICAL_EXECUTION_FREEZE: actual measurements are PHYSICAL.",
        "Models below are planning envelopes only.",
        "",
    ]
    for p in EVT_PROCEDURES:
        lines.append(f"## {p['id']}: {p['title']}")
        lines.append(f"- status: `{p['status']}`")
        lines.append(f"- instrumentation: {', '.join(p['instrumentation'])}")
        lines.append("")
    doc.write_text("\n".join(lines), encoding="utf-8")

    ok = len(models) == len(MODELS) and doc.exists() and all(p["status"] == "PHYSICAL_PENDING" for p in EVT_PROCEDURES)
    report = {
        "schema": "gunnchos.battery_thermal_handoff.v1",
        "ok": ok,
        "token": TOKEN_BATTERY_THERMAL if ok else None,
        "models": models,
        "evt_procedures": EVT_PROCEDURES,
        "doc": str(doc.relative_to(root)),
        "measured_physical": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "battery_thermal_handoff_incomplete",
    }
    out = root / "artifacts" / "continuation_ix" / "battery_thermal_handoff.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
