"""Tests for consent policy."""
from gunnchos_device_os.consent_policy import CONSENT_STATES, set_consent


def test_all_consent_states():
    assert len(CONSENT_STATES) == 5


def test_school_local_only():
    r = set_consent("s1", "local_only", "school")
    assert r["telemetry"]["local_only"] or r["consent_state"] == "local_only"
