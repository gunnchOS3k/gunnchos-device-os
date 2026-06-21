#!/usr/bin/env python3
"""Validate user-focused OS completeness."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.app_pack_manager import get_app_pack, list_app_packs
from gunnchos_device_os.journey_preset_engine import get_preset, list_presets
from gunnchos_device_os.persona_engine import get_persona, list_personas
from gunnchos_device_os.workspace_manager import get_workspace, list_workspaces

REQUIRED_PERSONAS = {
    "pre_k_learner", "early_reader", "middle_school_explorer", "high_school_student",
    "college_non_stem_student", "college_cs_stem_student", "graduate_researcher",
    "postdoctoral_researcher", "parent_guardian", "teacher_mentor", "artist", "writer",
    "musician", "gamer", "game_developer", "software_engineer", "hardware_engineer",
    "cybersecurity_learner", "wireless_6g_researcher", "library_community_user",
    "accessibility_first_user", "low_bandwidth_offline_user",
}

REQUIRED_PRESETS = {
    "scooter", "bicycle", "car", "studio", "arcade", "workshop", "laboratory",
    "spaceship", "guardian", "classroom", "library", "offline",
}


def main() -> int:
    errors: list[str] = []

    personas = set(list_personas())
    missing_personas = REQUIRED_PERSONAS - personas
    if missing_personas:
        errors.append(f"Missing personas: {sorted(missing_personas)}")

    presets = set(list_presets())
    missing_presets = REQUIRED_PRESETS - presets
    if missing_presets:
        errors.append(f"Missing journey presets: {sorted(missing_presets)}")

    for pid in personas:
        p = get_persona(pid)
        preset_id = p.get("default_journey_preset", "")
        if preset_id not in presets:
            errors.append(f"Persona {pid} references unknown preset {preset_id}")

    for preset_id in presets:
        preset = get_preset(preset_id)
        if not preset.get("allowed_apps"):
            errors.append(f"Preset {preset_id} missing allowed_apps")
        if not preset.get("accessibility_defaults"):
            errors.append(f"Preset {preset_id} missing accessibility_defaults")

    for pack_id in list_app_packs():
        pack = get_app_pack(pack_id)
        if "offline_support" not in pack:
            errors.append(f"App pack {pack_id} missing offline_support")
        if "privacy_warning" not in pack and pack.get("privacy_warning") is None:
            pass  # null is valid
        if "beginner_friendly_description" not in pack:
            errors.append(f"App pack {pack_id} missing beginner_friendly_description")

    for ws_id in list_workspaces():
        ws = get_workspace(ws_id)
        if not ws.get("quick_actions"):
            errors.append(f"Workspace {ws_id} missing quick_actions")

    demo_output = ROOT / "results/user_focused_os_demo_output.json"
    if not demo_output.exists():
        errors.append("Missing demo output: results/user_focused_os_demo_output.json")

    prd = ROOT / "product/USER_FOCUSED_OS_PRD.md"
    if not prd.exists():
        errors.append("Missing product/USER_FOCUSED_OS_PRD.md")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("validate_user_focused_os: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
