# Production Release Gate

**Gate ID:** `production_release` · **Status:** `not_started`

---

## Purpose

Fleet-scale production deployment with signing pipeline, staged rollout, rollback drills, and support SLA — distinct from GA single-user availability.

---

## Entry criteria

- GA release gate passed
- Field pilot gate passed (or waived with risk register entry)
- Production signing pipeline operational

---

## Required evidence

| Item | Status |
|------|--------|
| Production signing pipeline | not_started |
| Fleet update channel | not_started |
| MDM integration test report (if MDM claimed) | not_started |
| Production SBOM archive | not_started |
| Staged rollout runbook executed | not_started |
| 30-day rollback drill on fleet | not_started |
| Support SLA metrics | not_started |
| Repair parts catalog link | not_started |
| Production sign-off | not_started |

---

## Required tests

- Production regression suite
- Staged rollout canary → expand
- Rollback drill without data loss (per policy)

---

## Allowed claims (when passed)

- Production release on supported hardware
- Documented fleet update and support policy

---

## Forbidden claims (without evidence)

- Production MDM deployed (without integration report)
- Accessibility certified and validated on hardware (without report)
- Zero-downtime fleet guarantee

---

## Owner

Operations + release engineering
