"""Persistent diagnostics log — redaction + OTel hooks."""
from __future__ import annotations

from gunnchos_device_os.diagnostics_log import (
    DiagnosticsLog,
    OTelHooks,
    redact,
    try_attach_opentelemetry,
)
from gunnchos_device_os import security_event_log


def test_redact_nested_sensitive_keys():
    payload = {
        "action": "login",
        "password": "secret",
        "nested": {"token": "abc", "ok": 1},
        "list": [{"email": "a@b.c"}, "plain"],
    }
    out = redact(payload)
    assert out["password"] == "[REDACTED]"
    assert out["nested"]["token"] == "[REDACTED]"
    assert out["nested"]["ok"] == 1
    assert out["list"][0]["email"] == "[REDACTED]"
    assert out["list"][1] == "plain"


def test_persistent_jsonl(tmp_path):
    path = tmp_path / "events.jsonl"
    hooks_seen: list[dict] = []
    log = DiagnosticsLog(path=path, hooks=OTelHooks(on_log=hooks_seen.append))
    rec = log.log("boot", {"action": "start", "password": "nope"})
    assert rec["mock"] is False
    assert rec["persistent"] is True
    assert rec["details"]["password"] == "[REDACTED]"
    assert path.exists()
    rows = log.read()
    assert len(rows) == 1
    assert rows[0]["event_type"] == "boot"
    assert hooks_seen and hooks_seen[0]["event_type"] == "boot"


def test_span_hooks(tmp_path):
    starts: list[tuple] = []
    ends: list[tuple] = []
    log = DiagnosticsLog(
        path=tmp_path / "s.jsonl",
        hooks=OTelHooks(
            on_span_start=lambda n, a: starts.append((n, a)) or {"span": n},
            on_span_end=lambda s, a: ends.append((s, a)),
        ),
    )
    with log.span("dock.attach", {"device": "hh"}):
        log.log("inside", {"ok": True})
    assert starts and starts[0][0] == "dock.attach"
    assert ends
    types = [r["event_type"] for r in log.read()]
    assert "span_start" in types and "span_end" in types


def test_try_attach_opentelemetry_graceful():
    hooks = OTelHooks()
    result = try_attach_opentelemetry(hooks)
    assert "attached" in result
    # Either attached or cleanly reported missing SDK — both acceptable.
    assert result["attached"] in (True, False)


def test_security_event_log_persistent_path(tmp_path):
    security_event_log.clear_events(reset_persistent=True)
    security_event_log.configure_persistent_log(tmp_path / "sec.jsonl")
    security_event_log.log_event("auth", {"message_content": "secret", "action": "ok"})
    events = security_event_log.get_events()
    assert events[-1]["details"]["message_content"] == "[REDACTED]"
    assert events[-1]["details"]["action"] == "ok"
    assert events[-1]["mock"] is False
    security_event_log.clear_events(reset_persistent=True)
