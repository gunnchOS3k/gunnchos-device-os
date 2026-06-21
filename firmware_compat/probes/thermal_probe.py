"""Thermal zone probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, path_exists, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    indicators: dict[str, Any] = {"host_os": host, "device_id": device_id}

    if use_fixture:
        return probe_result(
            "pass",
            message="Thermal zones from fixture/thermal_zone_stub",
            indicators={**indicators, "source": "fixture", "thermal_zone_stub": True},
        )

    if host == "linux":
        tz = path_exists("/sys/class/thermal/thermal_zone0")
        count = len(list(__import__("pathlib").Path("/sys/class/thermal").glob("thermal_zone*"))) if path_exists("/sys/class/thermal") else 0
        indicators["thermal_zones"] = count
        status = "pass" if tz else "warn"
        msg = f"Host thermal zones: {count}"
    elif host in ("darwin", "windows"):
        status, msg = "warn", f"{host} host thermal — harness stub only"
    else:
        status, msg = "skip", "Unknown host for thermal probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2))
