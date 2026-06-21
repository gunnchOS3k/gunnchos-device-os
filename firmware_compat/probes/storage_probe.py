"""Storage enumeration probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, load_device_profile_fields, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    profile = load_device_profile_fields(device_id) if device_id else {}
    storage = (profile.get("profile") or {}).get("storage", {})
    indicators: dict[str, Any] = {
        "host_os": host,
        "device_id": device_id,
        "profile_storage": storage,
    }

    if use_fixture:
        return probe_result(
            "pass",
            message="Storage expectations from fixture/profile",
            indicators={**indicators, "source": "fixture"},
        )

    if host == "linux":
        block = __import__("pathlib").Path("/sys/block")
        disks = [p.name for p in block.iterdir()] if block.exists() else []
        indicators["block_devices"] = disks[:10]
        status = "pass" if disks else "warn"
        msg = f"Host block devices: {len(disks)}"
    elif host in ("darwin", "windows"):
        status, msg = "warn", f"{host} host storage — NVMe contract checked in harness"
    else:
        status, msg = "skip", "Unknown host for storage probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe("ds_xl_coder"), indent=2))
