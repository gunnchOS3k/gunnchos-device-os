# Mode Transition Rules

**Status:** device OS alpha · enforced in `gunnchos_device_os/mode_policy.py`  
**Config:** `config/modes.yaml` → `transition_rules`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## API

```python
from gunnchos_device_os.mode_policy import can_transition

result = can_transition(
    from_mode="School",
    to_mode="Developer",
    profile_type="middle_school",
    guardian_approved=False,
    consent_given=False,
)
# result["allowed"], result["user_message"], result["technical_log"]
```

---

## Rule: child_to_unrestricted

**Config:**

```yaml
child_to_unrestricted:
  requires_guardian_approval: true
  blocked_without_approval: [Developer, Admin, Workshop, Laboratory, Spaceship]
```

**Profile types affected:** `child`, `pre_k`, `elementary`, `middle_school`

**Behavior:** Transition to any blocked mode without `guardian_approved=True` returns:

- `allowed: False`
- `reason: guardian_approval_required`
- User message: "A guardian must approve switching to this mode."

---

## Rule: school_library_silent_admin

**Config:**

```yaml
school_library_silent_admin:
  blocked_transitions: [Admin, Developer]
  requires_explicit_consent: true
```

**From modes:** School, Library, Guardian

**Behavior:** Transition to Admin or Developer without `consent_given=True` returns:

- `allowed: False`
- `reason: explicit_consent_required`
- User message: "School and library devices need explicit approval for admin or developer modes."

---

## Rule: telemetry_requires_consent

**Config:**

```yaml
telemetry_requires_consent:
  modes_requiring_consent: [Research Measurement, Laboratory, Developer]
```

**Behavior:** If transitioning to a listed mode without consent:

- `allowed: True` (mode switch permitted)
- `telemetry_blocked_until_consent: True`
- User message: "This mode needs your consent before any telemetry starts."

Telemetry gating is separate from mode block — aligns with `consent_policy.py`.

---

## Rule: research_no_private_payload

**Config:**

```yaml
research_no_private_payload:
  blocked_data: [private_packet_capture, message_content, keystroke_logging]
```

Enforced via `research_mode_policy()` — applies to Research Measurement and Laboratory workflows.

---

## Allowed transition (default)

When no rule blocks:

```python
{
    "allowed": True,
    "user_message": "Switched to {to_mode}.",
    "technical_log": "mode_transition_ok:from={from} to={to}",
}
```

---

## Guardian policy overlap

`guardian_policy.approve_mode()` independently checks Developer/Admin/Workshop/Laboratory for age bands with `mode_approval: true`.

Both layers should agree in production; alpha tests cover both modules separately.

---

## Test matrix

| Test | File |
|------|------|
| Child → Developer blocked | `test_mode_policy.py::test_child_blocked_without_guardian` |
| School → Admin blocked | `test_mode_policy.py::test_school_admin_blocked` |
| Research payload rule | `test_mode_policy.py::test_research_no_private_payload` |

---

## Future rules (not implemented)

- Time-based play window from guardian config
- Geofence-based mode lock
- Fleet MDM forced mode

---

## Related documents

- [MODE_POLICY_MATRIX.md](MODE_POLICY_MATRIX.md)
- [MODES_OVERVIEW.md](MODES_OVERVIEW.md)
- [GUARDIAN_CONTROLS.md](GUARDIAN_CONTROLS.md)
