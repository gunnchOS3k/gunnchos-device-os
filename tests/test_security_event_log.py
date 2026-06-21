"""Tests for security event log."""
from gunnchos_device_os.security_event_log import clear_events, get_events, log_event


def test_redacts_sensitive():
    clear_events()
    log_event("test", {"message_content": "secret", "action": "ok"})
    ev = get_events()[-1]
    assert ev["details"]["message_content"] == "[REDACTED]"
    assert ev["details"]["action"] == "ok"
