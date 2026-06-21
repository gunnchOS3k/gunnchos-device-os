# Consent and Telemetry

**Status:** device OS alpha · opt-in consent states  
**Module:** `gunnchos_device_os/consent_policy.py`  
**Config:** `config/privacy_defaults.yaml` → `consent_states`, `telemetry_categories`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Consent states

| State | Meaning | Typical telemetry |
|-------|---------|-------------------|
| `not_asked` | User has not been prompted | Off until prompt |
| `denied` | User declined | Off, local-only |
| `local_only` | Local diagnostics only | local_diagnostics, device only |
| `opt_in_aggregate` | Aggregated usage opt-in | aggregate_usage |
| `opt_in_research` | Research metadata opt-in | research_measurement_metadata |

Defined in `CONSENT_STATES` tuple in `consent_policy.py`.

---

## API

```python
from gunnchos_device_os.consent_policy import set_consent, research_requires_consent

r = set_consent("user-1", "denied", profile_type="child")
# consent_state, telemetry dict, user_message, mock: True

research_requires_consent("research", "not_asked")  # True
```

---

## Telemetry categories

| Category | Description |
|----------|-------------|
| none | No telemetry collected |
| local_diagnostics | Local-only diagnostic logs |
| aggregate_usage | Aggregated opt-in usage metrics |
| research_measurement_metadata | Research session metadata with consent |
| crash_reports_placeholder | Placeholder with consent |

---

## Profile × consent behavior

`get_telemetry_policy(profile_type, consent_state)`:

| Condition | Result |
|-----------|--------|
| consent `denied` | enabled: False, local_only: True |
| child / pre_k / elementary | always enabled: False, category: none |
| requires_explicit_consent + not_asked | enabled: False, consent_required: True |
| opt_in_* states | enabled based on prefix match |

---

## Mode integration

Modes in `telemetry_requires_consent`:

- Research Measurement
- Laboratory
- Developer

Mode switch may proceed but telemetry blocked until consent — see [MODE_TRANSITION_RULES.md](MODE_TRANSITION_RULES.md).

---

## Edge-IO integration

`edge_io_contract.start_field_session(..., consent=False)` blocks session start.

---

## User messages

Consent changes return plain-language `user_message` from `_consent_message()` — e.g. "Telemetry is off. Your data stays on this device."

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_consent_policy.py tests/test_privacy_security_model.py
```

---

## Claim boundary

No real telemetry backend or analytics pipeline ships in alpha. Fleet panels show **synthetic** data only.
