#!/usr/bin/env python3
"""Validate accessibility coverage across presets and themes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.accessibility_manager import SUPPORTED_FEATURES, get_defaults, validate_coverage
from gunnchos_device_os.journey_preset_engine import list_presets
from gunnchos_device_os.theme_manager import get_theme, list_themes

REQUIRED_SETTINGS = {"high_contrast", "large_text", "reduced_motion", "keyboard_navigation", "controller_navigation", "touch_navigation"}


def main() -> int:
    errors: list[str] = []

    global_settings = get_defaults()
    missing_global = validate_coverage(global_settings)
    if missing_global:
        errors.append(f"Global accessibility missing: {missing_global}")

    for preset_id in list_presets():
        settings = get_defaults(preset_id)
        missing = validate_coverage(settings)
        if missing:
            errors.append(f"Preset {preset_id} accessibility missing: {missing}")
        for req in REQUIRED_SETTINGS:
            if req not in settings:
                errors.append(f"Preset {preset_id} missing required setting: {req}")

    for theme_id in list_themes():
        theme = get_theme(theme_id)
        if not theme.get("accessibility_notes"):
            errors.append(f"Theme {theme_id} missing accessibility_notes")

    if len(SUPPORTED_FEATURES) < 16:
        errors.append(f"Expected at least 16 supported features, got {len(SUPPORTED_FEATURES)}")

    if errors:
        print("ACCESSIBILITY VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("validate_accessibility_coverage: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
