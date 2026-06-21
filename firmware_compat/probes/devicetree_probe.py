"""DeviceTree path probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, path_exists, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    indicators: dict[str, Any] = {"host_os": host, "device_id": device_id}

    if use_fixture:
        return probe_result(
            "pass",
            message="DeviceTree descriptor referenced via fixture",
            indicators={**indicators, "source": "fixture"},
        )

    if host == "linux":
        dt = path_exists("/proc/device-tree", "/sys/firmware/devicetree")
        indicators["devicetree_present"] = dt
        status = "pass" if dt else "warn"
        msg = "DeviceTree present (ARM/embedded host)" if dt else "No DeviceTree — x86 UEFI host typical"
    elif host in ("darwin", "windows"):
        status, msg = "warn", "DeviceTree not applicable on this host OS"
    else:
        status, msg = "skip", "Unknown host for DeviceTree probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2))
