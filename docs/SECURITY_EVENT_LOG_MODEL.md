# Security Event Log Model

**Status:** device OS alpha · in-memory redacted log  
**Module:** `gunnchos_device_os/security_event_log.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

Provide a **minimal security event log** for admin and security-relevant actions with automatic redaction of sensitive fields.

---

## API

```python
from gunnchos_device_os.security_event_log import log_event, get_events, clear_events

log_event("mode_transition", {"action": "ok", "message_content": "secret"})
events = get_events(limit=50)
clear_events()
```

---

## Redaction rules

Keys in `_SENSITIVE_KEYS` are replaced with `"[REDACTED]"`:

- `password`
- `message_content`
- `private_payload`
- `keystroke`
- `location`

All other keys pass through unchanged.

---

## Entry schema

```json
{
  "event_type": "string",
  "details": { "key": "value or [REDACTED]" },
  "mock": true
}
```

---

## Planned event types (not exhaustive)

| event_type | Source module |
|------------|---------------|
| `mode_transition` | mode_policy (future hook) |
| `consent_change` | consent_policy (future hook) |
| `deploy_attempt` | deploy_contract (future hook) |
| `edge_io_session` | edge_io_contract (future hook) |
| `guardian_decision` | guardian_policy (future hook) |
| `admin_login` | Admin mode (future) |

Alpha: callers must invoke `log_event()` explicitly — no automatic hooks wired.

---

## Storage

| Property | Alpha value |
|----------|-------------|
| Persistence | In-memory list `_EVENTS` only |
| Process restart | Cleared |
| Export | Not implemented |
| Tamper evidence | Not implemented |

---

## Admin mode alignment

Admin mode telemetry category: `audit_only` — intended consumer of this log in production.

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_security_event_log.py
```

Verifies redaction of `message_content` while preserving non-sensitive fields.

---

## Related documents

- [GUARDIAN_AUDIT_LOG_MODEL.md](GUARDIAN_AUDIT_LOG_MODEL.md) — guardian-specific audit UX
- [THREAT_MODEL.md](THREAT_MODEL.md)
- [PRIVACY_SECURITY_LIMITATIONS.md](PRIVACY_SECURITY_LIMITATIONS.md)

---

## Claim boundary

Not a SIEM integration or tamper-evident audit trail — research prototype only.
