# Guardian Audit Log Model

**Status:** device OS alpha · placeholder only  
**Related:** `guardian_controls.py` (`audit_log: "placeholder"`), `security_event_log.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

Define what a **guardian audit log** would record for family and school transparency — without claiming a production audit pipeline exists today.

---

## Planned event types

| event_type | Description | PII allowed |
|------------|-------------|-------------|
| `guardian_app_request` | Child requested unapproved app | App ID only |
| `guardian_app_decision` | Guardian approved/denied app | App ID, decision |
| `guardian_mode_request` | Mode escalation requested | Mode name |
| `guardian_mode_decision` | Guardian approved/denied mode | Mode name, decision |
| `screen_time_warning` | Approaching daily limit | Duration aggregate |
| `play_window_denied` | Play outside allowed window | Time only |
| `emergency_unlock` | PIN/biometric unlock used | No child content |
| `deploy_guardian_approval` | Deploy approved for child target | Package type, target class |

---

## Log entry schema (planned)

```json
{
  "timestamp": "ISO8601",
  "event_type": "guardian_mode_decision",
  "profile_id": "child-1",
  "age_band": "elementary",
  "details": {
    "mode": "Developer",
    "approved": true,
    "actor": "guardian_profile_id"
  },
  "mock": true
}
```

**Forbidden in details:** message_content, browsing history URLs with query params, keystrokes, location (unless explicit opt-in research).

Aligns with `security_event_log._SENSITIVE_KEYS` redaction list.

---

## Current alpha behavior

| Component | Audit behavior |
|-----------|----------------|
| `guardian_controls.py` | Returns `"audit_log": "placeholder"` |
| `guardian_defaults.yaml` | `audit_log: placeholder` |
| `security_event_log.py` | General security events with redaction — not guardian-specific UI |

---

## Retention (planned)

| Profile | Retention |
|---------|-----------|
| Family guardian | 90 days local |
| School admin | 1 year aggregate (no content) |
| Research | Not stored by default |

Not implemented in alpha.

---

## Guardian-facing UX (planned)

- Chronological list with plain-language summaries
- Filter by app/mode/deploy
- Export CSV for school conferences (aggregate only)

---

## Integration with security event log

```python
from gunnchos_device_os.security_event_log import log_event

log_event("guardian_mode_decision", {
    "mode": "Developer",
    "approved": True,
    "message_content": "should be redacted",
})
```

Sensitive keys become `[REDACTED]`.

---

## Claim boundary

Audit log is a **data model sketch**. No persistent guardian audit store exists in alpha.

See [GUARDIAN_LIMITATIONS.md](GUARDIAN_LIMITATIONS.md).
