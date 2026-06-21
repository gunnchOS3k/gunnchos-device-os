"""UEFI / firmware environment probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, path_exists, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    indicators: dict[str, Any] = {"host_os": host, "use_fixture": use_fixture}

    if use_fixture:
        return probe_result(
            "pass",
            message="UEFI indicators from explicit fixture/profile",
            indicators={**indicators, "source": "fixture"},
        )

    if host == "linux":
        efi = path_exists("/sys/firmware/efi", "/boot/efi")
        indicators["efi_sysfs"] = efi
        status = "pass" if efi else "warn"
        msg = "EFI sysfs present" if efi else "No EFI sysfs — BIOS/VM or container"
    elif host == "darwin":
        indicators["platform"] = "apple_silicon_or_intel"
        status, msg = "warn", "macOS host — UEFI is host firmware, not gunnchOS target"
    elif host == "windows":
        indicators["firmware_type"] = "host_uefi_typical"
        status, msg = "warn", "Windows host — UEFI probe is host-environment only"
    else:
        status, msg = "skip", "Unknown host OS for UEFI probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe(), indent=2))
