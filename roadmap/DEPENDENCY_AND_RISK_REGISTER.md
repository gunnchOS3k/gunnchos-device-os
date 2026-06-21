# Dependency and Risk Register

**Last updated:** 2026-06-21 · complements [../release_gates/RELEASE_RISK_REGISTER.md](../release_gates/RELEASE_RISK_REGISTER.md)

---

## External dependencies

| ID | Dependency | Required for | Owner repo | Status | Impact if late |
|----|------------|--------------|------------|--------|----------------|
| D-001 | Student 14.5 reference hardware | RC install smoke, GA validation | hardware-industrial-design | blocked | RC slips |
| D-002 | Handheld Hybrid EVT | Gaming/thermal GA | hardware-industrial-design | blocked | GA handheld waived |
| D-003 | DS-XL Coder prototype | Deploy e2e | hardware-industrial-design | in_progress | Deploy claims mock-only |
| D-004 | GA signing key ceremony | RC+ signing | Security / Ops | not_started | RC blocked |
| D-005 | edge-io-measurement-node stable API | Edge-IO integration tests | edge-io-measurement-node | partial | Task 17 mock-only |
| D-006 | waike-research-ops LMS | WAIKE sync beyond cache | waike-research-ops | not_started | Task 18 YAML-only |
| D-007 | Windows CI agent | WSL dry-run tests | CI infra | unknown | Task 19 partial |
| D-008 | Steam partner policy | Real Steam launch | Valve/partner | not_started | Gaming stays mock |

---

## Internal dependencies

| ID | Dependency | Blocks |
|----|------------|--------|
| I-001 | CI demo generation (task 1) | Reliable pytest on clean checkout |
| I-002 | Installer pipeline (task 2) | All RC artifacts |
| I-003 | Launcher e2e (task 13) | RC UX confidence |
| I-004 | Security checklist (task 11) | RC sign-off |
| I-005 | Hardware matrix validator (task 9) | Compatibility report draft |

---

## Risk summary (top 5)

| Rank | Risk | Mitigation |
|------|------|------------|
| 1 | No installable image | RC backlog tasks 2–4, 7, 8 |
| 2 | Hardware not available | YAML validation first; pilot waiver for wearables |
| 3 | Over-claiming GA | Gate validators + claim boundary docs |
| 4 | Security review gap | Task 11 + SBOM task 5 |
| 5 | Launcher mock ≠ production | Task 13 e2e + installer integration |

---

## Assumptions

1. Windows-first OS-layer remains primary ship path through GA
2. Bare-metal image deferred until hardware program defines it
3. Mock Steam/media acceptable through RC; partner docs required for certification claims
4. Child privacy defaults remain opt-in telemetry unless guardian enables

---

## Review schedule

- Weekly: RC backlog burn-down
- Per gate transition: full register review
- After hardware EVT arrival: re-rate D-001–D-003

---

## Claim boundary

Dependencies listed here explain why GA release is **not met** today. Absence of hardware or signing evidence **must not** be papered over in release claims.
