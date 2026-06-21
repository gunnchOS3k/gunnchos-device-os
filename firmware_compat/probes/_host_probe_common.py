"""Shared helpers for host firmware probes — no root, no hardware claims."""
from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROBE_VERSION = "0.1.0-harness"
CLAIM = (
    "Host-side firmware probe — not physical gunnchOS hardware validation."
)


def detect_host_os() -> str:
    s = sys.platform
    if s.startswith("linux"):
        return "linux"
    if s == "darwin":
        return "darwin"
    if s in ("win32", "cygwin"):
        return "windows"
    return "unknown"


def path_exists(*paths: str | Path) -> bool:
    return any(Path(p).exists() for p in paths)


def probe_result(
    status: str,
    *,
    simulated: bool = True,
    message: str = "",
    indicators: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "simulated": simulated,
        "message": message,
        "host_os": detect_host_os(),
        "indicators": indicators or {},
        "claim_boundary": CLAIM,
    }


def load_device_profile_fields(device_id: str) -> dict[str, Any]:
    """Load minimal fields from hardware_compat device profile if present."""
    profile_path = ROOT / "hardware_compat" / "device_profiles" / f"{device_id}.yaml"
    if not profile_path.exists():
        return {"device_id": device_id, "profile_found": False}
    try:
        import yaml
        data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        return {"device_id": device_id, "profile_found": True, "profile": data}
    except Exception as exc:  # noqa: BLE001
        return {"device_id": device_id, "profile_found": False, "error": str(exc)}
