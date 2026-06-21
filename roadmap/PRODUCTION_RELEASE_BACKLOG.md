# Production Release Backlog

**Target gate:** `production_release` · **Status:** not started · requires GA

---

## Epic P-1 — Fleet operations

| ID | Task | Priority |
|----|------|----------|
| P-101 | Production signing pipeline + HSM | P0 |
| P-102 | Fleet update channel (stable + staged rollout) | P0 |
| P-103 | 30-day fleet rollback drill | P0 |
| P-104 | Update health metrics dashboard | P1 |
| P-105 | School/library managed channel | P1 |

---

## Epic P-2 — MDM and enterprise (optional claims)

| ID | Task | Priority |
|----|------|----------|
| P-201 | MDM integration test report | P0 if MDM claimed |
| P-202 | IT admin console for policy push | P1 |
| P-203 | Asset inventory sync | P2 |

**Note:** Do **not** claim production MDM deployed without P-201 evidence.

---

## Epic P-3 — Field pilot → production

| ID | Task | Priority |
|----|------|----------|
| P-301 | Field pilot completion report | P0 |
| P-302 | Incident response SLA operational | P0 |
| P-303 | Production support tier staffing | P0 |
| P-304 | Repair parts catalog live | P1 |
| P-305 | Pilot → production enrollment migration | P1 |

---

## Epic P-4 — Observability and compliance

| ID | Task | Priority |
|----|------|----------|
| P-401 | Consented telemetry pipeline (if offered) | P1 |
| P-402 | Production SBOM archive retention | P0 |
| P-403 | Annual security review cadence | P1 |

---

## Production exit criteria

- [ ] GA gate passed
- [ ] Field pilot gate passed or waived
- [ ] Fleet rollback drill evidence archived
- [ ] [../release_gates/PRODUCTION_RELEASE_GATE.md](../release_gates/PRODUCTION_RELEASE_GATE.md) sign-off

---

## Claim boundary

Production release enables fleet-scale claims only with ops evidence. Does **not** claim accessibility certified on hardware or secure boot complete on all devices without per-SKU reports.
