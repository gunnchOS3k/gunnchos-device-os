# Release Blockers

**Active blockers for RC and GA claims** · Updated 2026-06-21

---

## P0 — blocks RC claim

| ID | Blocker | Owner | Target resolution |
|----|---------|-------|-------------------|
| B-001 | No signed installable bundle | Release eng | RC backlog #2–4 |
| B-002 | No checksum/SBOM pipeline | Release eng | RC backlog #4–5 |
| B-003 | Installable image not proven on reference hardware | QA + HW | RC backlog #2, #9 |
| B-004 | Security review checklist incomplete | Security | RC backlog #11 |
| B-005 | No RC UAT execution report | QA | RC backlog #12 |
| B-006 | Launcher e2e tests missing | UX | RC backlog #13 |

---

## P1 — blocks GA claim

| ID | Blocker | Owner | Target resolution |
|----|---------|-------|-------------------|
| B-101 | Hardware compatibility not physically proven (all GA SKUs) | HW + QA | GA backlog |
| B-102 | Accessibility validation report missing on hardware | QA | RC backlog #10 |
| B-103 | Update/rollback not production-proven | Release eng | RC backlog #8 |
| B-104 | Recovery bundle not built | Release eng | RC backlog #8 |
| B-105 | Support runbook incomplete | Support | GA backlog |
| B-106 | Performance/battery baselines not recorded | HW + QA | GA backlog |

---

## P2 — blocks production release

| ID | Blocker | Owner |
|----|---------|-------|
| B-201 | No production signing pipeline | Ops |
| B-202 | No fleet staged rollout drill | Ops |
| B-203 | MDM integration not tested (if claimed) | Programs |

---

## Resolved / mitigated

| ID | Blocker | Resolution |
|----|---------|------------|
| B-000 | CI demo output missing in clean checkout | CI workflow + self-generating test (in progress on branch) |

---

## Not blockers (explicit)

- User-focused alpha exists — **not a blocker**
- Shippable requirements documentation — **not a blocker**
- Mock Steam/media routes — blocker only for partner certification **claims**, not alpha

---

## Claim boundary

These blockers exist because **GA release is not met** and installable image is **not yet proven**. Do not override without signed waiver.
