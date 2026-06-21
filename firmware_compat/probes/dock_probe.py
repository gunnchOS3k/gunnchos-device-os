"""Dock / USB-C alt-mode probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, load_device_profile_fields, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    profile = load_device_profile_fields(device_id) if device_id else {}
    dock_supported = (profile.get("profile") or {}).get("dock", {}).get("supported", False)
    indicators: dict[str, Any] = {
        "host_os": host,
        "device_id": device_id,
        "profile_dock_supported": dock_supported,
    }

    if use_fixture:
        return probe_result(
            "pass" if dock_supported else "warn",
            message="Dock expectations from fixture/profile",
            indicators={**indicators, "source": "fixture", "dock_attached": True},
        )

    # Host cannot detect gunnchOS dock without fixture
    if host == "linux":
        usb = __import__("pathlib").Path("/sys/bus/usb/devices")
        indicators["usb_devices"] = len(list(usb.iterdir())) if usb.exists() else 0
        status = "warn"
        msg = "Host USB present — gunnchOS dock not detected without fixture"
    else:
        status, msg = "warn", "Dock hotplug not observable for gunnchOS on this host"

    if device_id and not dock_supported:
        status = "warn"
        msg = "Profile marks dock unsupported — N/A for this SKU"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe("student_14_5"), indent=2))
