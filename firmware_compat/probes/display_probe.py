"""Display enumeration probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, load_device_profile_fields, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    profile = load_device_profile_fields(device_id) if device_id else {}
    indicators: dict[str, Any] = {
        "host_os": host,
        "device_id": device_id,
        "profile_display": (profile.get("profile") or {}).get("display"),
    }

    if use_fixture:
        return probe_result(
            "pass",
            message="Display expectations from fixture/profile",
            indicators={**indicators, "source": "fixture"},
        )

    if host == "linux":
        drm = __import__("pathlib").Path("/sys/class/drm")
        cards = list(drm.glob("card*")) if drm.exists() else []
        indicators["drm_cards"] = len(cards)
        status = "pass" if cards else "warn"
        msg = f"Found {len(cards)} DRM card(s) on host"
    elif host == "darwin":
        indicators["display_services"] = "quartz_host"
        status, msg = "warn", "macOS host display — not gunnchOS panel"
    elif host == "windows":
        status, msg = "warn", "Windows host display — not gunnchOS panel"
    else:
        status, msg = "skip", "Unknown host for display probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe("student_14_5"), indent=2))
