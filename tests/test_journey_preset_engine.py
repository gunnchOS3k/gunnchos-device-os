"""Tests for journey preset engine."""
from gunnchos_device_os.journey_preset_engine import get_preset, list_presets


REQUIRED = {"scooter", "bicycle", "car", "studio", "arcade", "workshop",
            "laboratory", "spaceship", "guardian", "classroom", "library", "offline"}


def test_all_presets_exist():
    assert REQUIRED.issubset(set(list_presets()))


def test_preset_has_required_fields():
    for pid in list_presets():
        p = get_preset(pid)
        assert p.get("allowed_apps"), f"{pid} missing allowed_apps"
        assert p.get("accessibility_defaults"), f"{pid} missing accessibility_defaults"
        assert p.get("onboarding_text"), f"{pid} missing onboarding_text"
        assert p.get("exit_paths"), f"{pid} missing exit_paths"
