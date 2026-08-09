"""Device Management / Diagnostics application."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import tempfile
import time

CLAIM_BOUNDARY = (
    "Digital device management surfaces over real runtime service APIs. "
    "Not production MDM and not physical hardware attestation."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_device_management(*, role: str = "student") -> dict[str, Any]:
    ui = _repo_root() / "apps/device_management/index.html"
    surfaces = {
        "hardware_inventory": "hal.inventory",
        "storage": "diagnostics.storage",
        "battery": "hal.power_state",
        "display": "display.outputs",
        "connectivity": "connectivity.status",
        "ring": "ring.calibrate",
        "update_state": "updater.status",
        "recovery": "recovery.status",
        "logs": "diagnostics.query",
        "privacy_permissions": "permissions.summary",
        "fleet": "fleet_agent.report",
    }
    live: dict[str, Any] = {}
    err = None
    try:
        from gunnchos_device_os.runtime.ipc import IpcRuntimePlane

        sock = Path(tempfile.gettempdir()) / f"gchos-dm-{os.getpid()}"
        plane = IpcRuntimePlane(socket_dir=sock, enable_http=False)
        try:
            plane.start_services(
                [
                    "hal",
                    "display",
                    "connectivity",
                    "ring",
                    "updater",
                    "recovery",
                    "diagnostics",
                    "permissions",
                    "fleet_agent",
                    "identity",
                ]
            )
            live["hal.inventory"] = plane.call("hal", "inventory")
            live["hal.power_state"] = plane.call("hal", "power_state")
            live["display.outputs"] = plane.call("display", "outputs")
            live["connectivity.status"] = plane.call("connectivity", "list_bearers")
            live["ring.calibrate"] = plane.call("ring", "calibrate")
            live["updater.status"] = plane.call("updater", "check")
            live["recovery.status"] = plane.call("recovery", "playbook")
            live["diagnostics.query"] = plane.call("diagnostics", "query", limit=3)
            live["permissions.summary"] = plane.call("permissions", "list_grants")
            live["fleet_agent.report"] = plane.call("fleet_agent", "report")
        finally:
            plane.stop()
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        live = {"error": err, "mode": "snapshot_only"}

    bundle = {
        "schema": "gunnchos.diagnostics_bundle.v1",
        "created_at": time.time(),
        "role": role,
        "surfaces": list(surfaces.keys()),
        "live_keys": list(live.keys()),
        "mock": False,
    }
    ok = ui.exists() and err is None and "error" not in live
    live_summary = {}
    for k, v in live.items():
        if k == "error":
            continue
        if isinstance(v, dict) and "ok" in v:
            live_summary[k] = v.get("ok")
        else:
            live_summary[k] = True
    return {
        "ok": ok,
        "app_id": "device_dashboard",
        "entry": "apps/device_management/index.html",
        "surfaces": surfaces,
        "bundle": bundle,
        "live": live_summary,
        "ui_present": ui.exists(),
        "mock": False,
        "stub_content": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
