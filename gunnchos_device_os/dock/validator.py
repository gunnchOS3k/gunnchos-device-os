"""Dock validation recorder (before/after metrics)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.identity import sha256_json, utc_now_iso

from .collector import collect_host_dock_signals
from .continuity import DockContinuityEngine
from .simulator import STATUS_PHYSICAL_PENDING, STATUS_SIM_PASS, run_dock_simulation


def run_dock_validation(
    *,
    simulate: bool = True,
    collect_host: bool = True,
    out_path: Path | str | None = None,
) -> dict[str, Any]:
    host = collect_host_dock_signals() if collect_host else {}
    if simulate:
        sim = run_dock_simulation()
        engine = DockContinuityEngine(device_id=sim["report"]["device_id"])
        before = engine.observe(phase="validation_before")
        engine.attach("val-dock-001")
        after = engine.observe(phase="validation_after")
        engine.safe_undock()
        evidence = {
            "schema": "gunnchos.dock_evidence.v1",
            "timestamp": utc_now_iso(),
            "device_id": engine.device_id,
            "dock_id": "val-dock-001",
            "ports": after.get("ports"),
            "display_before": before.get("display"),
            "display_after": after.get("display"),
            "inputs_before": before.get("inputs"),
            "inputs_after": after.get("inputs"),
            "network_before": before.get("network"),
            "network_after": after.get("network"),
            "apps": after.get("apps"),
            "session_id": after.get("session_id"),
            "save_checksum": after.get("save_checksum"),
            "audio": after.get("audio"),
            "power": after.get("power"),
            "latencies_ms": engine.latencies_ms,
            "errors": engine.errors,
            "host_signals": host,
            "simulation": sim,
            "status_tokens": [STATUS_SIM_PASS, STATUS_PHYSICAL_PENDING],
            "physical_dock": False,
            "claim_boundary": (
                "Validation CLI recorded simulation metrics. "
                "PHYSICAL_DOCK_EVIDENCE_PENDING."
            ),
        }
    else:
        evidence = {
            "schema": "gunnchos.dock_evidence.v1",
            "timestamp": utc_now_iso(),
            "host_signals": host,
            "simulation": False,
            "status_tokens": [STATUS_PHYSICAL_PENDING],
            "physical_dock": False,
            "claim_boundary": "Host collector only; no physical dock success claimed.",
        }

    evidence["evidence_checksum"] = sha256_json(
        {k: v for k, v in evidence.items() if k != "evidence_checksum"}
    )

    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return evidence
