"""Tests for user profile schema."""
from gunnchos_device_os.user_profile_schema import UserProfile


def test_profile_roundtrip():
    p = UserProfile(
        user_id="u1", display_name="Test", age_band="high_school",
        persona="high_school_student", journey_preset="car",
    )
    restored = UserProfile.from_dict(p.to_dict())
    assert restored.user_id == "u1"
    assert restored.persona == "high_school_student"


def test_profile_validate():
    p = UserProfile(user_id="", display_name="", age_band="adult", persona="", journey_preset="")
    errors = p.validate()
    assert len(errors) >= 3
