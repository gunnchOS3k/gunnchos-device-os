"""ACPI table / path probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, path_exists, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    indicators: dict[str, Any] = {"host_os": host, "device_id": device_id}

    if use_fixture:
        return probe_result(
            "pass",
            message="ACPI descriptor referenced via fixture",
            indicators={**indicators, "source": "fixture"},
        )

    if host == "linux":
        acpi = path_exists("/sys/firmware/acpi", "/proc/acpi")
        indicators["acpi_sysfs"] = acpi
        status = "pass" if acpi else "warn"
        msg = "ACPI sysfs available" if acpi else "ACPI sysfs not found"
    elif host in ("darwin", "windows"):
        status, msg = "warn", f"{host} host ACPI does not represent gunnchOS board DSDT"
    else:
        status, msg = "skip", "Unknown host for ACPI probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2))
