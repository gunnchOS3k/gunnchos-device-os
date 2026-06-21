"""Tests for accessibility manager."""
from gunnchos_device_os.accessibility_manager import SUPPORTED_FEATURES, apply_settings, get_defaults


def test_supported_features():
    assert len(SUPPORTED_FEATURES) >= 16


def test_high_contrast_large_text_reduced_motion():
    settings = apply_settings({"high_contrast": True, "large_text": True, "reduced_motion": True})
    assert settings["high_contrast"] is True
    assert settings["large_text"] is True
    assert settings["reduced_motion"] is True


def test_input_navigation_support():
    settings = get_defaults()
    assert settings.get("keyboard_navigation") is not None
    assert settings.get("controller_navigation") is not None
    assert settings.get("touch_navigation") is not None
