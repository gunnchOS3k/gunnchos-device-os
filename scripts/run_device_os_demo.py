#!/usr/bin/env python3
"""Run EVT-1 OS alpha demo and write JSON output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.mode_manager import get_mode_policy
from gunnchos_device_os.policy_engine import evaluate
from gunnchos_device_os.hardware_abstraction import get_device_profile
from gunnchos_device_os.telemetry_consent import ConsentState
from gunnchos_device_os.updater import check_for_update
from gunnchos_device_os.rollback import rollback_to
from gunnchos_device_os.steam_integration import detect_steam_installed, launch_uri

def main():
    device = "Student14"
    profile = "student"
    mode = "School"
    pol = get_mode_policy(mode)
    out = {
        "evt1_alpha": True,
        "mock": True,
        "device_profile": get_device_profile(device),
        "user_profile": profile,
        "active_mode": mode,
        "allowed_apps": pol["allowed_apps"],
        "blocked_apps": pol["blocked_apps"],
        "telemetry_policy": pol["telemetry"],
        "steam_blocked_in_school": evaluate(profile, mode, "steam")["allowed"] is False,
        "developer_steam_policy": evaluate("developer", "Developer", "steam"),
        "play_steam_policy": evaluate("developer", "Play", "steam"),
        "media_netflix_route": __import__("gunnchos_device_os.media_apps", fromlist=["open_route"]).open_route("netflix"),
        "telemetry_export": ConsentState(opted_in=True).export(),
        "update_status": check_for_update("0.0.9-evt0"),
        "rollback_status": rollback_to("0.0.9-evt0"),
        "steam_detected": detect_steam_installed(),
        "steam_launch_uri": launch_uri("0"),
        "claim_boundary": "EVT-1 OS alpha prototype — not shipping OS",
    }
    dest = ROOT / "results/device_os_evt1_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
