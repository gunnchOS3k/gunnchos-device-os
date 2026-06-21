# Support and Repair Requirements

**Status:** partial troubleshooting docs · production support SLA **not active**

> Repairability aligns with hardware PRD targets. OS must support diagnosable, recoverable field operation.

---

## Support tiers

| Tier | Scope |
|------|-------|
| Self-serve | Reset, rollback, safe mode, FAQ |
| School IT | Shared device wipe, offline bundle, asset tracking |
| Guardian | Profile controls, approval, audit export |
| Manufacturer | RMA, parts, warranty |

---

## Required support artifacts (GA)

- Release notes with known issues
- Troubleshooting guide (`docs/DEPLOY_TROUBLESHOOTING.md` partial)
- Recovery runbook ([BOOT_AND_RECOVERY_REQUIREMENTS.md](BOOT_AND_RECOVERY_REQUIREMENTS.md))
- Support ticket template with device class + OS version fields

---

## Repair workflow

1. Diagnose via device health dashboard (mock → production)
2. Attempt software recovery before RMA
3. Log repair action in security event log (IT/admin)
4. Replaceable battery/storage per hardware program (hardware repo)

---

## Device health signals

| Signal | Use |
|--------|-----|
| Storage low | Warn before update fail |
| Battery health | Throttle or notify (handheld) |
| Thermal events | Performance governor |
| Update failure count | Offer rollback |

Alpha: `device_health.py` mock.

---

## Field pilot and production

- Field pilot: dedicated support playbook ([../release_gates/FIELD_PILOT_GATE.md](../release_gates/FIELD_PILOT_GATE.md))
- Production: SLA metrics in production release gate

---

## Evidence before GA

- Support runbook exercised in pilot
- Repair/RMA path documented with hardware team
- Device health dashboard shows actionable items on reference hardware

---

## Claim boundary

Support/repair **requirements** are defined. No active production support SLA or nationwide repair network is claimed.
