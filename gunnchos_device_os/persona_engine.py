"""Persona engine — recommend presets, apps, and safety from user profile."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_accessibility_defaults, load_personas
from .user_profile_schema import UserProfile


def list_personas() -> list[str]:
    return list(load_personas().get("personas", {}).keys())


def get_persona(persona_id: str) -> dict[str, Any]:
    personas = load_personas().get("personas", {})
    if persona_id not in personas:
        raise ValueError(f"Unknown persona: {persona_id}")
    return {"id": persona_id, **personas[persona_id]}


def recommend_for_profile(profile: UserProfile) -> dict[str, Any]:
    persona = get_persona(profile.persona)
    preset = persona.get("default_journey_preset", profile.journey_preset)
    a11y = load_accessibility_defaults().get("presets", {}).get(preset, {})
    return {
        "persona": profile.persona,
        "default_journey_preset": preset,
        "default_apps": persona.get("default_apps", []),
        "default_widgets": persona.get("default_widgets", []),
        "safety_settings": {
            "privacy_level": persona.get("privacy_level", profile.privacy_level),
            "guardian_required": persona.get("guardian_required", profile.guardian_required),
            "blocked_apps": persona.get("blocked_apps", []),
        },
        "accessibility_settings": {**a11y, **{n: True for n in profile.accessibility_needs}},
        "onboarding_copy": persona.get("onboarding_copy", f"Welcome, {profile.display_name}!"),
        "blocked_apps": persona.get("blocked_apps", []),
        "recommended_next_step": persona.get("recommended_next_step", "Explore your home screen"),
    }
