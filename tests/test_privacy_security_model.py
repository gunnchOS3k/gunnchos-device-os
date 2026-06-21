"""Tests for privacy/security model."""
from gunnchos_device_os.consent_policy import research_requires_consent, set_consent
from gunnchos_device_os.privacy_security_model import get_profile_defaults, get_telemetry_policy, request_delete, request_export


def test_no_telemetry_for_child():
    t = get_telemetry_policy("child", "not_asked")
    assert t["enabled"] is False
    assert t["category"] == "none"


def test_research_requires_consent():
    assert research_requires_consent("research", "not_asked") is True


def test_export_delete_paths():
    assert request_export("u1")["path"]
    assert request_delete("u1")["path"]


def test_consent_states():
    r = set_consent("u1", "denied", "child")
    assert r["consent_state"] == "denied"
