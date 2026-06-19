#!/usr/bin/env python3
"""Run EVT-1 OS alpha demo — full PRD acceptance walkthrough output."""
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
from gunnchos_device_os.steam_integration import detect_steam_installed, launch_uri, list_placeholder_games
from gunnchos_device_os.launcher import launch_app, list_launchable
from gunnchos_device_os.parental_controls import school_restrictions, content_report
from gunnchos_device_os.device_health import get_health_snapshot
from gunnchos_device_os.input_mapper import get_bindings, controller_first_nav_enabled
from gunnchos_device_os.wsl_dev_tools import detect_wsl, checklist as wsl_checklist
from gunnchos_device_os.media_apps import open_route
from gunnchos_device_os.waike_integration import list_offline_lessons, deploy_lesson
from gunnchos_device_os.gunnchai_integration import tutor_session_start
from gunnchos_device_os.dock_manager import dock_state
from gunnchos_device_os.accessibility import get_a11y_defaults
from gunnchos_device_os.performance_governor import get_performance_profile


def run_walkthrough() -> dict:
    device = "Student14"
    profile = "student"
    school_mode = "School"
    dev_mode = "Developer"
    play_mode = "Play"
    media_mode = "Media"
    school_pol = get_mode_policy(school_mode)

    consent = ConsentState(opted_in=True)
    consent.record("session_minutes", 45)

    return {
        "evt1_alpha": True,
        "mock": True,
        "claim_boundary": "EVT-1 OS alpha prototype — not shipping OS",
        "device_profile": get_device_profile(device),
        "user_profile": profile,
        "active_mode": school_mode,
        "allowed_apps": school_pol["allowed_apps"],
        "blocked_apps": school_pol["blocked_apps"],
        "telemetry_policy": school_pol["telemetry"],
        "update_status": check_for_update("0.0.9-evt0"),
        "rollback_status": rollback_to("0.0.9-evt0"),
        "walkthrough": {
            "1_device_profile": device,
            "2_user_profile": profile,
            "3_school_mode": school_mode,
            "4_steam_blocked_in_school": evaluate(profile, school_mode, "steam")["allowed"] is False,
            "5_developer_mode": {
                "mode": dev_mode,
                "vscode": launch_app("developer", dev_mode, "vscode"),
                "wsl_checklist": wsl_checklist(),
                "wsl_detect": detect_wsl(),
            },
            "6_play_mode": {
                "mode": play_mode,
                "steam_launch": launch_app("developer", play_mode, "steam"),
                "steam_uri": launch_uri("0"),
                "placeholder_games": list_placeholder_games(),
            },
            "7_media_mode": {
                "mode": media_mode,
                "netflix_route": open_route("netflix"),
            },
            "8_telemetry_export": consent.export(),
            "9_update_and_rollback": {
                "update": check_for_update("0.0.9-evt0"),
                "rollback": rollback_to("0.0.9-evt0"),
            },
            "10_dsxl_coder_mode": launch_app("student", "Coder", "vscode"),
        },
        "parental_controls": school_restrictions(school_mode),
        "content_report": content_report(profile, "inappropriate_chat"),
        "device_health": get_health_snapshot(device),
        "input_mapper": get_bindings("handheld_default"),
        "controller_first": controller_first_nav_enabled("HandheldHybrid"),
        "waike_lessons": list_offline_lessons(),
        "waike_deploy": deploy_lesson("python_starter_pack", profile),
        "gunnchai_tutor": tutor_session_start(profile, "wireless_basics"),
        "dock": dock_state(connected=True),
        "accessibility": get_a11y_defaults(),
        "performance": get_performance_profile("school"),
        "launchable_apps_sample": list_launchable(profile, school_mode)[:5],
        "steam_detected": detect_steam_installed(),
        "boot_path_documented": "docs/BOOT_AND_DEMO_PATH.md",
        "installable_image_path": "docs/BOOT_AND_DEMO_PATH.md#evt-1-alpha-path",
    }


def main() -> int:
    out = run_walkthrough()
    dest = ROOT / "results/device_os_evt1_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
