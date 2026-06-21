"""Tests for guardian controls and policy."""
from gunnchos_device_os.guardian_controls import apply_guardian_defaults, enable_guardian_controls
from gunnchos_device_os.guardian_policy import approve_app, approve_mode, get_age_band_policy


def test_age_band_defaults():
    p = get_age_band_policy("elementary")
    assert p["app_approval"] is True
    assert p["private_content_inspection"] is False


def test_app_approval():
    assert approve_app("steam", "elementary", [])["approved"] is False


def test_mode_approval():
    assert approve_mode("Developer", "elementary")["approved"] is False


def test_enable_controls():
    r = enable_guardian_controls("child-1", "elementary")
    assert r["enabled"] is True
    assert apply_guardian_defaults("elementary")["mock"] is True
