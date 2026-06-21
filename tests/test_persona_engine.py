"""Tests for persona engine."""
from gunnchos_device_os.journey_preset_engine import list_presets
from gunnchos_device_os.persona_engine import get_persona, list_personas, recommend_for_profile
from gunnchos_device_os.user_profile_schema import UserProfile


def test_all_personas_exist():
    assert len(list_personas()) >= 22


def test_every_persona_maps_to_preset():
    presets = set(list_presets())
    for pid in list_personas():
        p = get_persona(pid)
        assert p["default_journey_preset"] in presets, f"{pid} missing preset"


def test_recommend_for_profile():
    profile = UserProfile(
        user_id="t", display_name="T", age_band="high_school",
        persona="high_school_student", journey_preset="car",
    )
    rec = recommend_for_profile(profile)
    assert "default_journey_preset" in rec
    assert "onboarding_copy" in rec
