"""Onboarding wizard — first-run decision tree."""
from __future__ import annotations

from typing import Any

from .accessibility_manager import apply_settings
from .app_pack_manager import get_app_pack
from .guardian_controls import apply_guardian_defaults
from .persona_engine import get_persona, list_personas
from .user_profile_schema import UserProfile
from .workspace_manager import get_workspace


QUESTIONS = [
    "Who is this device for?",
    "What do you want to do first?",
    "Do you want simple, guided, or full control?",
    "Do you need accessibility support?",
    "Will you use this offline?",
    "Are guardian controls needed?",
    "Do you want learning, creating, playing, working, researching, or all of them?",
]


def _map_persona(who: str) -> str:
    mapping = {
        "pre_k": "pre_k_learner",
        "child": "early_reader",
        "student": "high_school_student",
        "college": "college_cs_stem_student",
        "researcher": "graduate_researcher",
        "parent": "parent_guardian",
        "teacher": "teacher_mentor",
        "artist": "artist",
        "writer": "writer",
        "musician": "musician",
        "gamer": "gamer",
        "developer": "software_engineer",
    }
    return mapping.get(who, "high_school_student")


def _map_preset(goal: str, control: str) -> str:
    goal_map = {
        "learn": "bicycle",
        "create": "studio",
        "play": "arcade",
        "work": "car",
        "research": "laboratory",
        "all": "car",
    }
    preset = goal_map.get(goal, "scooter")
    if control == "power_user":
        return "spaceship"
    if control == "simple":
        return "scooter" if goal == "learn" else preset
    return preset


def run_onboarding(answers: dict[str, Any]) -> dict[str, Any]:
    persona_id = _map_persona(answers.get("who", "student"))
    if persona_id not in list_personas():
        persona_id = "high_school_student"
    persona = get_persona(persona_id)
    preset = _map_preset(answers.get("goal", "learn"), answers.get("control", "simple"))
    if answers.get("offline"):
        preset = "offline"
    if answers.get("guardian"):
        preset = "guardian" if answers.get("who") in ("pre_k", "child") else preset

    profile = UserProfile(
        user_id=answers.get("user_id", "new-user"),
        display_name=answers.get("display_name", "New User"),
        age_band=persona.get("age_band", "high_school"),
        persona=persona_id,
        journey_preset=preset,
        accessibility_needs=answers.get("accessibility_needs", []),
        guardian_required=bool(answers.get("guardian")),
        offline_first=bool(answers.get("offline")),
        skill_level=answers.get("skill_level", "beginner"),
        customization_depth=answers.get("control", "simple"),
    )

    pack_id = persona.get("default_app_pack", "learn_pack")
    workspace_id = persona.get("default_workspace", "homework_desk")
    a11y = apply_settings({n: True for n in profile.accessibility_needs})
    safety = apply_guardian_defaults(profile.age_band) if profile.guardian_required else {}

    return {
        "profile_json": profile.to_dict(),
        "recommended_journey_preset": preset,
        "selected_app_packs": [pack_id],
        "app_pack_details": get_app_pack(pack_id),
        "selected_workspace": workspace_id,
        "workspace_details": get_workspace(workspace_id),
        "accessibility_defaults": a11y,
        "safety_defaults": safety,
        "questions_answered": QUESTIONS,
    }
