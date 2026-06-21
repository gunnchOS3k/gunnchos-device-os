"""Tests for customization engine."""
from gunnchos_device_os.customization_engine import CustomizationEngine
from gunnchos_device_os.user_profile_schema import UserProfile


def test_theme_and_export():
    profile = UserProfile(
        user_id="c1", display_name="C", age_band="adult",
        persona="writer", journey_preset="studio",
    )
    engine = CustomizationEngine(profile)
    theme = engine.change_theme("writer_focus")
    assert theme["theme_id"] == "writer_focus"
    exported = engine.export_profile()
    assert "profile" in exported
    engine.import_profile(exported)
    assert engine.profile.user_id == "c1"


def test_reset_safe_defaults():
    profile = UserProfile(
        user_id="c2", display_name="C2", age_band="adult",
        persona="gamer", journey_preset="arcade", customization_depth="power_user",
    )
    engine = CustomizationEngine(profile)
    result = engine.reset_to_safe_defaults()
    assert result["profile"]["customization_depth"] == "simple"
