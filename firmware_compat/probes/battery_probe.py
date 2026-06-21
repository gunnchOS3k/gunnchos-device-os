"""Battery status probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, path_exists, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    indicators: dict[str, Any] = {"host_os": host, "device_id": device_id}

    if use_fixture:
        return probe_result(
            "pass",
            message="Battery status from fixture/smart_battery_stub",
            indicators={**indicators, "source": "fixture", "smart_battery_stub": True},
        )

    if host == "linux":
        bat = path_exists("/sys/class/power_supply/BAT0", "/sys/class/power_supply/BAT1")
        indicators["host_battery_sysfs"] = bat
        status = "pass" if bat else "warn"
        msg = "Host battery sysfs found" if bat else "No host battery — desktop/VM typical"
    elif host == "darwin":
        indicators["pmset_available"] = True
        status, msg = "warn", "macOS host battery — not gunnchOS smart battery"
    elif host == "windows":
        status, msg = "warn", "Windows host battery — harness uses stub contract"
    else:
        status, msg = "skip", "Unknown host for battery probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2))
