# Hardware Pilot Test Plan

**Status:** plan documented · **pilot not started**

Field pilot for hardware-compatible claims beyond lab DVT — school, home, and venue contexts.

Aligns with OS `release_gates/FIELD_PILOT_GATE.md` and hardware `pvt/PVT_PRODUCTION_TEST_PLAN.md`.

---

## Pilot objectives

1. Validate real-world mode switching and guardian policies on reference hardware
2. Validate Handheld gaming/dock behavior in home setting
3. Validate DS-XL deploy flow to Student targets in classroom
4. Validate Wearables/Arena marshal workflows in supervised venue
5. Collect failure data for boot fallbacks and support playbooks

---

## Pilot tiers

| Tier | Audience | SKUs | Duration |
|------|----------|------|----------|
| PT-1 | Internal dogfood | Student 14.5 | 2 weeks |
| PT-2 | Partner school (1 classroom) | Student 14.5, DS-XL | 4 weeks |
| PT-3 | Home gaming panel | Handheld Hybrid | 2 weeks |
| PT-4 | Supervised venue | Wearables / Arena | 1 event |

**Start with PT-1 only after P1 lab boot pass.**

---

## Entry criteria

| Criterion | Source |
|-----------|--------|
| HC-T1 boot pass for pilot SKU | [HARDWARE_COMPATIBILITY_TEST_PLAN.md](HARDWARE_COMPATIBILITY_TEST_PLAN.md) |
| Recovery tested once | lab checklist |
| Guardian controls documented | `docs/GUARDIAN_CONTROLS.md` |
| Known gaps communicated to pilot users | gap analysis |
| Consent/telemetry forms ready | `requirements/TELEMETRY_CONSENT_REQUIREMENTS.md` |

---

## Test scenarios

### PT-1 Internal dogfood (Student 14.5)

| ID | Scenario | Success metric |
|----|----------|----------------|
| PP-001 | Daily school mode login | no boot blockers |
| PP-002 | Developer mode WSL dry-run | completes or documented fail |
| PP-003 | Dock to external monitor | display stable 1 hour |
| PP-004 | Offline day | core apps usable |
| PP-005 | Guardian time window | policy enforced |

### PT-2 Classroom (Student + DS-XL)

| ID | Scenario | Success metric |
|----|----------|----------------|
| PP-010 | Teacher deploy lesson from DS-XL | target receives package |
| PP-011 | 20-seat simultaneous boot | <5% failure rate |
| PP-012 | Marshal/guardian override | audit log entry |

### PT-3 Home gaming (Handheld)

| ID | Scenario | Success metric |
|----|----------|----------------|
| PP-020 | Controller session 2 hours | no thermal shutdown |
| PP-021 | TV dock evening | display + audio OK |
| PP-022 | Steam path (if enabled) | launch or documented gap |

### PT-4 Venue (Wearables)

| ID | Scenario | Success metric |
|----|----------|----------------|
| PP-030 | Marshal-led arena session | no unsupervised Play |
| PP-031 | Developer mode blocked | engine blocker confirmed |
| PP-032 | Emergency stop / reset | marshal procedure works |

---

## Data collection

| Data type | Storage |
|-----------|---------|
| Boot success/fail counts | pilot report |
| Thermal/battery anecdotes | linked to DVT gaps |
| Guardian audit samples | redacted logs |
| User feedback | survey template |
| Defects | issue tracker |

---

## Exit criteria (field pilot gate)

| Criterion | Threshold |
|-----------|-----------|
| Critical boot failures | zero unresolved |
| Guardian safety defects | zero open |
| Arena unsupervised Play | zero incidents |
| Deploy success rate (PT-2) | ≥95% |
| Signoff | [HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md](HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md) pilot section |

---

## Claim boundary

Pilot plan is **not executed**. Field pilot pass is required for R3 venue/school claims, not for R1 simulation tier.

Hardware repo PVT remains authoritative for factory-scale quality; this pilot covers OS UX on reference units.
