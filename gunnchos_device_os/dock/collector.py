"""Real-device dock signal collector — detects actual capabilities without vendor assumptions."""
from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any

from gunnchos_device_os.identity import new_device_id, utc_now_iso


def collect_host_dock_signals() -> dict[str, Any]:
    """Observe host USB/display hints without assuming Pixel or USB-C DP Alt Mode."""
    system = platform.system().lower()
    signals: dict[str, Any] = {
        "collected_at": utc_now_iso(),
        "device_id_local": new_device_id("host"),
        "platform": platform.system(),
        "arch": platform.machine(),
        "assumes_pixel": False,
        "assumes_usb_c_dp_alt_mode": False,
        "observed": {},
        "capabilities_detected": [],
        "notes": [],
    }

    observed: dict[str, Any] = {}
    caps: list[str] = []

    # USB enumeration hints (Linux sysfs / macOS ioreg availability only)
    linux_usb = Path("/sys/bus/usb/devices")
    if linux_usb.exists():
        entries = [p.name for p in linux_usb.iterdir()]
        observed["usb_sysfs_count"] = len(entries)
        caps.append("usb_bus_visible")
        signals["notes"].append("Linux USB sysfs visible; no dock identity assumed.")
    else:
        observed["usb_sysfs_count"] = None

    # Display: env only — never invent DP Alt Mode
    import os

    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        caps.append("host_display_server_env")
        observed["display_server_env"] = True
    else:
        observed["display_server_env"] = False
        signals["notes"].append("No DISPLAY/WAYLAND_DISPLAY; external dock display unknown.")

    # Optional tools presence (not executed with heavy probes)
    for tool in ("ioreg", "system_profiler", "lsusb", "usb-devices"):
        observed[f"tool_{tool}"] = bool(shutil.which(tool))

    if system == "darwin":
        signals["notes"].append(
            "macOS host: use system_profiler/ioreg manually for physical dock evidence; "
            "collector does not assume Thunderbolt/DP Alt Mode."
        )
    elif system == "windows":
        signals["notes"].append(
            "Windows host: collector records platform only; PnP dock IDs require physical run."
        )

    # Explicit non-claims
    observed["dock_attached_proven"] = False
    observed["external_display_via_dock_proven"] = False
    observed["dp_alt_mode_proven"] = False

    signals["observed"] = observed
    signals["capabilities_detected"] = caps
    signals["status_tokens"] = ["PHYSICAL_DOCK_EVIDENCE_PENDING"]
    signals["claim_boundary"] = (
        "Collector reports observed host signals only. "
        "PHYSICAL_DOCK_EVIDENCE_PENDING — no physical dock success claimed."
    )
    return signals
