#!/usr/bin/env python3
"""Check required user experience files exist."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "product/USER_FOCUSED_OS_PRD.md",
    "product/PERSONA_MATRIX.md",
    "product/JOURNEY_PRESETS.md",
    "docs/USER_FOCUSED_OS_ARCHITECTURE.md",
    "docs/SCOOTER_TO_SPACESHIP_MODEL.md",
    "docs/ACCESSIBILITY_AND_INCLUSION.md",
    "docs/CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md",
    "gunnchos_device_os/user_profile_schema.py",
    "gunnchos_device_os/persona_engine.py",
    "gunnchos_device_os/journey_preset_engine.py",
    "gunnchos_device_os/customization_engine.py",
    "gunnchos_device_os/accessibility_manager.py",
    "gunnchos_device_os/app_pack_manager.py",
    "gunnchos_device_os/workspace_manager.py",
    "gunnchos_device_os/onboarding_wizard.py",
    "gunnchos_device_os/guardian_controls.py",
    "gunnchos_device_os/creator_mode_manager.py",
    "gunnchos_device_os/offline_mode_manager.py",
    "gunnchos_device_os/edge_case_policy.py",
    "config/personas.yaml",
    "config/journey_presets.yaml",
    "config/app_packs.yaml",
    "config/themes.yaml",
    "config/workspaces.yaml",
    "config/accessibility_defaults.yaml",
    "config/edge_cases.yaml",
    "scripts/run_user_focused_os_demo.py",
    "scripts/validate_user_focused_os.py",
    "demo/user_focused_os_walkthrough.md",
]


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        print("MISSING FILES:")
        for m in missing:
            print(f"  - {m}")
        return 1
    print(f"check_user_experience_files: OK ({len(REQUIRED)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
