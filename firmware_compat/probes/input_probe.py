"""Input device probe."""
from __future__ import annotations

from typing import Any

from ._host_probe_common import detect_host_os, load_device_profile_fields, probe_result


def probe(device_id: str = "", *, use_fixture: bool = False) -> dict[str, Any]:
    host = detect_host_os()
    profile = load_device_profile_fields(device_id) if device_id else {}
    inp = (profile.get("profile") or {}).get("input", {})
    indicators: dict[str, Any] = {
        "host_os": host,
        "device_id": device_id,
        "profile_input": inp,
    }

    if use_fixture:
        return probe_result(
            "pass",
            message="Input expectations from fixture/profile",
            indicators={**indicators, "source": "fixture"},
        )

    if host == "linux":
        ev = __import__("pathlib").Path("/dev/input")
        count = len(list(ev.iterdir())) if ev.exists() else 0
        indicators["input_nodes"] = count
        status = "pass" if count else "warn"
        msg = f"Host input nodes: {count}"
    elif host in ("darwin", "windows"):
        status, msg = "warn", f"{host} host input — not gunnchOS keyboard/touch mapping"
    else:
        status, msg = "skip", "Unknown host for input probe"

    return probe_result(status, message=msg, indicators=indicators)


if __name__ == "__main__":
    import json
    print(json.dumps(probe("handheld_hybrid"), indent=2))
