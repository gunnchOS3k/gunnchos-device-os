# Engineering Milestones

**Timeline:** indicative · subject to hardware program dependencies

---

## M0 — Alpha complete (2026 Q2) ✅

| Deliverable | Owner | Status |
|-------------|-------|--------|
| OS alpha modules + tests | OS team | done |
| User-focused 11-scenario demo | UX | done |
| Issue backlog operational pass | OS team | done |
| Shippable requirements package | Release | done |
| CI validators | CI | done |

---

## M1 — Beta ready (2026 Q3)

| Deliverable | Owner | Status |
|-------------|-------|--------|
| Installer prototype | Release eng | not_started |
| Version manifest CI | Release eng | planned |
| Launcher e2e smoke | UX | not_started |
| Beta gate sign-off | Release | not_started |

**Dependency:** M0 complete

---

## M2 — Release candidate (2026 Q4)

| Deliverable | Owner | Status |
|-------------|-------|--------|
| Signed bundle + checksums + SBOM | Release eng | not_started |
| Recovery demo + bundle | OS core | not_started |
| RC test reports (UAT, a11y draft, security) | QA | not_started |
| RC backlog 20 tasks closed (P0) | All | in_progress |
| RC gate sign-off | Release | not_started |

**Dependency:** M1 + reference hardware for install smoke

---

## M3 — GA release (2027 Q1)

| Deliverable | Owner | Status |
|-------------|-------|--------|
| Hardware validation 3 SKUs | HW + QA | not_started |
| GA-signed installer | Release eng | not_started |
| Performance + battery baselines | HW + QA | not_started |
| Support runbooks | Support | in_progress |
| GA gate sign-off | Release | not_started |

**Dependency:** M2 + EVT/DVT hardware availability

---

## M4 — Field pilot (2027 Q2)

| Deliverable | Owner | Status |
|-------------|-------|--------|
| 3–5 enrolled pilot sites | Programs | not_started |
| Field support playbook | Support | not_started |
| Pilot UAT report | QA | not_started |

**Dependency:** M3

---

## M5 — Production release (2027 H2+)

| Deliverable | Owner | Status |
|-------------|-------|--------|
| Fleet update channel | Ops | not_started |
| Production rollback drill | Ops | not_started |
| Production gate sign-off | Ops + Release | not_started |

**Dependency:** M4

---

## Critical path

```text
CI fix → installer → signed RC bundle → HW validation → GA → pilot → production
         ↑                              ↑
    launcher e2e                   reference devices (HW program)
```

---

## Cross-repo milestones

| Repo | Dependency |
|------|------------|
| gunnchos-hardware-industrial-design | EVT/DVT devices, PRD specs |
| edge-io-measurement-node | Live session tests (task 17) |
| waike-research-ops | LMS sync (post-RC) |

---

## Claim boundary

Milestone dates are planning targets. Missing hardware or signing ceremony delays GA — **does not** authorize early GA claims.
