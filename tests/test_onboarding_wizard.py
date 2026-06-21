"""Tests for onboarding wizard."""
import json

from gunnchos_device_os.onboarding_wizard import run_onboarding


def test_onboarding_produces_valid_profile():
    result = run_onboarding({
        "who": "student", "goal": "learn", "control": "guided",
        "display_name": "Test", "user_id": "test-1",
    })
    assert "profile_json" in result
    profile = result["profile_json"]
    assert profile["user_id"] == "test-1"
    assert profile["journey_preset"]
    json.dumps(profile)


def test_guardian_onboarding():
    result = run_onboarding({
        "who": "child", "goal": "learn", "control": "simple",
        "guardian": True, "display_name": "Kid", "user_id": "kid-1",
    })
    assert result["profile_json"]["guardian_required"] is True
