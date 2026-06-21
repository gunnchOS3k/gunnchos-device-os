#!/usr/bin/env python3
"""Hardware compatibility demo — 12 scenarios."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.deploy_contract import deploy_package
from gunnchos_device_os.edge_io_contract import start_field_session
from gunnchos_device_os.hardware_boot_readiness import evaluate_boot_readiness
from gunnchos_device_os.hardware_compatibility_report import scenario_report


def _s(device, persona="", preset="", mode="", app_pack="", **kw):
    r = scenario_report(device, persona=persona, journey_preset=preset, mode=mode, app_pack=app_pack, **kw)
    r["selected_profile"] = persona
    r["selected_preset"] = preset
    r["selected_mode"] = mode
    r["selected_app_pack"] = app_pack
    r["pass_warn_fail"] = r["status"]
    r["safety_privacy_notes"] = "Guardian/consent policies apply where noted"
    return r


def main() -> int:
    scenarios = [
        _s("student_14_5", "high_school_student", "car", "School"),
        _s("student_14_5", "college_cs_stem_student", "workshop", "Developer", app_pack="cs_student_pack"),
        _s("student_14_5", "writer", "studio", "Studio", app_pack="write_pack"),
        _s("handheld_hybrid", "gamer", "arcade", "Play", app_pack="game_pack"),
        _s("handheld_hybrid", "library_community_user", "offline", "Media"),
        {"scenario": "ds_xl_coding_lesson", "device_id": "ds_xl_coder", "boot": evaluate_boot_readiness("ds_xl_coder"),
         "compat": _s("ds_xl_coder", "college_cs_stem_student", "workshop", "Coder", app_pack="cs_student_pack")},
        {"scenario": "ds_xl_deploy_handheld", "deploy": deploy_package(
            "ds_xl_coder", "handheld_hybrid", "python_project", "local_wifi",
            user_consent=True, guardian_approved=True)},
        _s("wearables_arena_set", "gamer", "arcade", "Play", marshal_control=True),
        _s("wearables_arena_set", "software_engineer", "spaceship", "Developer"),
        {"scenario": "research_measurement_consent", "edge_io_blocked": start_field_session("u1", "student_14_5", consent=False),
         "edge_io_started": start_field_session("u1", "student_14_5", consent=True, research_operator=True),
         "compat": _s("student_14_5", "postdoctoral_researcher", "laboratory", "Research Measurement", consent=True)},
        {"scenario": "accessibility_all_devices", "results": [
            _s(d, "accessibility_first_user", "car", "School", accessibility_needs=["high_contrast", "large_text"])
            for d in ("student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set")
        ]},
        {"scenario": "offline_all_devices", "results": [
            _s(d, "library_community_user", "offline", "Offline", offline_first=True)
            for d in ("student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set")
        ]},
    ]
    out = {
        "hardware_compatibility_demo": True,
        "simulated": True,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "claim_boundary": "Profile-based compatibility demo — not physical hardware boot",
    }
    dest = ROOT / "results/hardware_compatibility_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
