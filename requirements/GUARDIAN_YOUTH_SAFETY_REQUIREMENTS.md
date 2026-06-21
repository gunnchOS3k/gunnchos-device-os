# Guardian and Youth Safety Requirements

**Status:** policy stubs + mock controls · **production MDM not deployed**

> Youth safety for child profiles. See `guardian_policy.py`, `guardian_controls.py`, `docs/GUARDIAN_CONTROLS.md`. This document does not claim production MDM deployed without integration evidence.

---

## Age bands

- Config-driven bands in `config/guardian_defaults.yaml`
- Policy differs by band: app install, mode access, telemetry, deploy targets

---

## Guardian approval flows

| Action | Child profile |
|--------|---------------|
| Install app | Approval request → guardian UI |
| Mode transition (e.g., Play) | May require approval |
| Deploy to device | Restricted transports |
| Telemetry opt-in | Guardian only |
| Factory reset | Guardian PIN |

---

## Audit and transparency

- Guardian audit log model (`docs/GUARDIAN_AUDIT_LOG_MODEL.md`)
- Child sees age-appropriate explanation when blocked
- No hidden parental monitoring beyond disclosed features

---

## Content and time controls

- Screen time schedules
- App deny/allow lists
- Play/media restrictions per [GAMING_MEDIA_REQUIREMENTS.md](GAMING_MEDIA_REQUIREMENTS.md)

---

## COPPA / youth privacy

- Child telemetry off by default
- Data minimization per [SECURITY_PRIVACY_REQUIREMENTS.md](SECURITY_PRIVACY_REQUIREMENTS.md)
- Legal compliance is **separate review** — not claimed by OS repo

---

## Alpha evidence

| Artifact | Status |
|----------|--------|
| `guardian_policy.py` | pytest |
| `guardian_controls.py` | prototype |
| Demo walkthrough | `demo/guardian_controls_walkthrough.md` |
| User-focused demo | Guardian controls scenario |

---

## Evidence before RC

- Guardian approval flow automated tests
- Audit log persistence tests
- UAT with guardian + child personas

---

## Forbidden claims

- Production MDM deployed
- COPPA certified without legal audit
- Guaranteed protection against all online harm

---

## Claim boundary

Guardian/youth safety **requirements** and alpha stubs exist. The repo does **not** claim production MDM deployed or certified youth safety compliance.
