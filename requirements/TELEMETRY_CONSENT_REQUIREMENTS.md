# Telemetry and Consent Requirements

**Status:** consent model proven in pytest · production telemetry pipeline **not deployed**

> See `consent_policy.py`, `telemetry_consent.py`, `docs/CONSENT_AND_TELEMETRY.md`.

---

## Consent principles

1. **Opt-in** for optional telemetry (default off for child profiles)
2. **Granular** categories: diagnostics, usage, crash, research (if ever offered)
3. **Revocable** at any time in settings
4. **Transparent** — plain-language descriptions; link to data policy
5. **No hidden channels** — all egress documented

---

## Consent states

| State | Telemetry | UI |
|-------|-----------|-----|
| Not asked | None optional | First-run prompt |
| Denied | None optional | Settings to reconsider |
| Limited | Crash only (if policy allows) | Category toggles |
| Full (adult) | User-selected categories | Category toggles |
| Guardian-managed | Guardian choice for child | Guardian app |

---

## Data minimization

- Field list in `config/privacy_defaults.yaml`
- No document contents, keystrokes, or screen recording in default telemetry
- Security events local unless explicitly exported

---

## Local-only mode

- Disables all optional cloud telemetry
- Core OS functions remain
- Research measurement mode requires explicit consent (`docs/RESEARCH_MEASUREMENT_MODE.md`)

---

## Export and delete

- Export consent history and telemetry queue metadata (design)
- Delete queued telemetry on revoke
- **Full production pipeline not proven**

---

## Alpha evidence

- `tests/test_consent_policy.py`
- `tests/test_privacy_security_model.py`
- Child telemetry off default tests

---

## Evidence before RC

- Consent UI walkthrough in UAT
- Revoke → no further send test (mock pipeline)
- Telemetry consent requirements cross-check in security review

---

## Claim boundary

Telemetry/consent **requirements** are defined with alpha mocks. No claim of production analytics fleet or compliance certification.
