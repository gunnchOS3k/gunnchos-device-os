#!/usr/bin/env python3
"""Validate every persona has a journey preset route."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.journey_preset_engine import list_presets
from gunnchos_device_os.onboarding_wizard import run_onboarding
from gunnchos_device_os.persona_engine import get_persona, list_personas

REQUIRED_PERSONAS = 22


def main() -> int:
    errors: list[str] = []
    personas = list_personas()

    if len(personas) < REQUIRED_PERSONAS:
        errors.append(f"Expected {REQUIRED_PERSONAS} personas, found {len(personas)}")

    presets = set(list_presets())
    for pid in personas:
        p = get_persona(pid)
        preset = p.get("default_journey_preset")
        if not preset:
            errors.append(f"Persona {pid} has no default_journey_preset")
        elif preset not in presets:
            errors.append(f"Persona {pid} preset {preset} not in journey presets")

    # Every persona should have onboarding route via wizard mapping
    sample = run_onboarding({"who": "student", "goal": "all", "control": "guided"})
    if "profile_json" not in sample:
        errors.append("Onboarding wizard does not produce profile_json")

    if errors:
        print("PERSONA VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"validate_persona_coverage: OK ({len(personas)} personas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
