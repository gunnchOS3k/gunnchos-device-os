#!/usr/bin/env python3
"""Export default profiles for each persona."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.onboarding_wizard import run_onboarding
from gunnchos_device_os.persona_engine import get_persona, list_personas
from gunnchos_device_os.user_profile_schema import UserProfile


PERSONA_WHO_MAP = {
    "pre_k_learner": "pre_k",
    "early_reader": "child",
    "high_school_student": "student",
    "college_cs_stem_student": "college",
    "graduate_researcher": "researcher",
    "parent_guardian": "parent",
    "teacher_mentor": "teacher",
    "artist": "artist",
    "writer": "writer",
    "musician": "musician",
    "gamer": "gamer",
    "software_engineer": "developer",
}


def main() -> int:
    out_dir = ROOT / "results/default_profiles"
    out_dir.mkdir(parents=True, exist_ok=True)

    for pid in list_personas():
        p = get_persona(pid)
        who = PERSONA_WHO_MAP.get(pid, "student")
        onboarding = run_onboarding({
            "who": who, "goal": "all", "control": "guided",
            "display_name": f"Default {pid}", "user_id": f"default-{pid}",
        })
        profile = UserProfile.from_dict(onboarding["profile_json"])
        profile.persona = pid
        profile.journey_preset = p.get("default_journey_preset", profile.journey_preset)
        payload = {
            "profile": profile.to_dict(),
            "onboarding": onboarding,
        }
        dest = out_dir / f"{pid}.json"
        dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Exported {len(list_personas())} profiles to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
