"""Network interface probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, load_device_profile_fields, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    profile = load_device_profile_fields(device_id) if device_id else {}
    net = (profile.get("profile") or {}).get("network", {})
    indicators: dict[str, Any] = {
        "host_os": host,
        "device_id": device_id,
        "profile_network": net,
    }

    if use_fixture:
        return probe_result(
            "pass",
            message="Network expectations from fixture/profile",
            indicators={**indicators, "source": "fixture", "wifi_stub": True},
        )

    if host == "linux":
        net_cls = __import__("pathlib").Path("/sys/class/net")
        ifaces = [p.name for p in net_cls.iterdir() if p.name != "lo"] if net_cls.exists() else []
        indicators["interfaces"] = ifaces[:10]
        status = "pass" if ifaces else "warn"
        msg = f"Host network interfaces: {len(ifaces)}"
    elif host in ("darwin", "windows"):
        status, msg = "warn", f"{host} host network — wifi_stub contract in harness"
    else:
        status, msg = "skip", "Unknown host for network probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe("wearables_arena_set"), indent=2))
