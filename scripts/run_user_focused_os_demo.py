#!/usr/bin/env python3
"""Run user-focused OS demo — scooter to spaceship walkthrough."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.accessibility_manager import apply_settings
from gunnchos_device_os.creator_mode_manager import get_creator_workflow
from gunnchos_device_os.customization_engine import CustomizationEngine
from gunnchos_device_os.guardian_controls import enable_guardian_controls
from gunnchos_device_os.journey_preset_engine import get_preset
from gunnchos_device_os.offline_mode_manager import enable_offline_mode
from gunnchos_device_os.onboarding_wizard import run_onboarding
from gunnchos_device_os.persona_engine import recommend_for_profile
from gunnchos_device_os.user_profile_schema import UserProfile
from gunnchos_device_os.workspace_manager import get_workspace


def _scenario(name: str, profile: UserProfile, extra: dict | None = None) -> dict:
    preset = get_preset(profile.journey_preset)
    rec = recommend_for_profile(profile)
    ws_id = rec.get("recommended_next_step", "")
    workspace = None
    try:
        persona_ws = json.loads(json.dumps(rec))
        ws_key = profile.persona.replace("_", " ")
    except Exception:
        ws_key = ""
    from gunnchos_device_os.persona_engine import get_persona
    persona = get_persona(profile.persona)
    workspace = get_workspace(persona.get("default_workspace", "homework_desk"))
    result = {
        "scenario": name,
        "profile": profile.to_dict(),
        "journey_preset": preset,
        "recommendations": rec,
        "workspace": workspace,
    }
    if extra:
        result.update(extra)
    return result


def run_demo() -> dict:
    scenarios = []

    # 1. Pre-K learner — Scooter Mode
    pre_k = UserProfile(
        user_id="demo-prek", display_name="Sam", age_band="pre_k",
        persona="pre_k_learner", journey_preset="scooter",
        guardian_required=True, skill_level="first_time_user", customization_depth="simple",
    )
    scenarios.append(_scenario("pre_k_scooter", pre_k))

    # 2. High school student — Car Mode
    hs = UserProfile(
        user_id="demo-hs", display_name="Jordan", age_band="high_school",
        persona="high_school_student", journey_preset="car",
        skill_level="intermediate", customization_depth="guided",
    )
    scenarios.append(_scenario("high_school_car", hs))

    # 3. Writer — Studio Mode
    writer = UserProfile(
        user_id="demo-writer", display_name="Alex", age_band="adult",
        persona="writer", journey_preset="studio",
        creative_interests=["writing"], skill_level="intermediate", customization_depth="guided",
    )
    writer_extra = get_creator_workflow("writer")
    scenarios.append(_scenario("writer_studio", writer, {"creator_workflow": writer_extra}))

    # 4. Musician — Music Studio
    musician = UserProfile(
        user_id="demo-musician", display_name="Riley", age_band="undergraduate",
        persona="musician", journey_preset="studio",
        creative_interests=["music"], skill_level="intermediate",
    )
    scenarios.append(_scenario("musician_studio", musician, {
        "creator_workflow": get_creator_workflow("musician"),
        "workspace": get_workspace("music_studio"),
    }))

    # 5. Artist — Art Table
    artist = UserProfile(
        user_id="demo-artist", display_name="Casey", age_band="adult",
        persona="artist", journey_preset="studio",
        creative_interests=["art"], skill_level="advanced",
    )
    scenarios.append(_scenario("artist_art_table", artist, {
        "creator_workflow": get_creator_workflow("artist"),
        "workspace": get_workspace("art_table"),
    }))

    # 6. Gamer — Arcade Mode
    gamer = UserProfile(
        user_id="demo-gamer", display_name="Taylor", age_band="high_school",
        persona="gamer", journey_preset="arcade",
        gaming_preferences=["casual", "controller"], skill_level="intermediate",
    )
    scenarios.append(_scenario("gamer_arcade", gamer))

    # 7. CS student — Workshop Mode
    cs = UserProfile(
        user_id="demo-cs", display_name="Morgan", age_band="undergraduate",
        persona="college_cs_stem_student", journey_preset="workshop",
        learning_goals=["coding"], skill_level="intermediate", customization_depth="full",
    )
    scenarios.append(_scenario("cs_workshop", cs))

    # 8. Researcher — Laboratory/Spaceship
    researcher = UserProfile(
        user_id="demo-researcher", display_name="Dr. Lee", age_band="postdoc",
        persona="postdoctoral_researcher", journey_preset="spaceship",
        work_goals=["wireless_experiments"], skill_level="expert", customization_depth="power_user",
    )
    lab = get_preset("laboratory")
    scenarios.append(_scenario("researcher_laboratory_spaceship", researcher, {
        "laboratory_preset": lab,
    }))

    # 9. Guardian controls
    guardian = enable_guardian_controls("demo-prek", "pre_k")
    scenarios.append({"scenario": "guardian_controls", "guardian": guardian})

    # 10. Offline library user
    offline_user = UserProfile(
        user_id="demo-library", display_name="Pat", age_band="adult",
        persona="library_community_user", journey_preset="offline",
        offline_first=True, skill_level="beginner",
    )
    scenarios.append(_scenario("offline_library", offline_user, {
        "offline_mode": enable_offline_mode("offline"),
    }))

    # 11. Accessibility-first user
    a11y_user = UserProfile(
        user_id="demo-a11y", display_name="Jordan A", age_band="adult",
        persona="accessibility_first_user", journey_preset="car",
        accessibility_needs=["high_contrast", "large_text", "reduced_motion"],
        skill_level="intermediate",
    )
    engine = CustomizationEngine(a11y_user)
    a11y_settings = apply_settings({
        "high_contrast": True, "large_text": True, "reduced_motion": True,
    })
    theme = engine.change_theme("high_contrast")
    scenarios.append(_scenario("accessibility_first", a11y_user, {
        "accessibility_settings": a11y_settings,
        "theme_applied": theme,
    }))

    # Onboarding sample
    onboarding = run_onboarding({
        "who": "student", "goal": "learn", "control": "guided",
        "accessibility_needs": [], "offline": False, "guardian": False,
        "display_name": "Demo Student", "user_id": "onboard-demo",
    })

    return {
        "user_focused_os_alpha": True,
        "claim_boundary": "User-focused OS alpha — not a finished shipping OS image",
        "scenarios": scenarios,
        "onboarding_sample": onboarding,
        "scenario_count": len(scenarios),
    }


def main() -> int:
    out = run_demo()
    dest = ROOT / "results/user_focused_os_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
