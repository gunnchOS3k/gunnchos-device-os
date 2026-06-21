"""Tests for mode policy transitions."""
from gunnchos_device_os.mode_policy import can_transition, research_mode_policy


def test_child_blocked_without_guardian():
    r = can_transition("School", "Developer", profile_type="child")
    assert r["allowed"] is False


def test_school_admin_blocked():
    r = can_transition("School", "Admin", consent_given=False)
    assert r["allowed"] is False


def test_research_no_private_payload():
    p = research_mode_policy()
    assert p["no_private_payload"]
