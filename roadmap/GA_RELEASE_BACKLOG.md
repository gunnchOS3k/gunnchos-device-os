# GA Release Backlog

**Target gate:** `ga_release` · **Status:** not started · depends on RC backlog completion

---

## Epic G-1 — Hardware validation

| ID | Task | Priority |
|----|------|----------|
| G-101 | Student 14.5 full compatibility test report | P0 |
| G-102 | Handheld Hybrid compatibility + thermal report | P0 |
| G-103 | DS-XL Coder deploy-on-hardware e2e | P0 |
| G-104 | Wearables waiver or pilot-only scope document | P1 |
| G-105 | Signed compatibility matrix publication | P0 |

---

## Epic G-2 — Install / update / recovery

| ID | Task | Priority |
|----|------|----------|
| G-201 | GA signing key ceremony | P0 |
| G-202 | Production-quality installer (GA-signed) | P0 |
| G-203 | Update + rollback drill per SKU | P0 |
| G-204 | Recovery bundle hardware drill | P0 |
| G-205 | Factory reset data wipe verification | P0 |

---

## Epic G-3 — QA and accessibility

| ID | Task | Priority |
|----|------|----------|
| G-301 | Full UAT on all 11 personas × GA SKUs | P0 |
| G-302 | Accessibility validation report on hardware | P0 |
| G-303 | Performance baselines recorded | P1 |
| G-304 | Battery/thermal handoff complete (handheld) | P1 |
| G-305 | GA regression suite frozen and archived | P0 |

---

## Epic G-4 — Security and compliance

| ID | Task | Priority |
|----|------|----------|
| G-401 | Security review sign-off | P0 |
| G-402 | Vulnerability disclosure policy published | P1 |
| G-403 | Secrets scan in CI | P1 |
| G-404 | SBOM archive for GA tag | P0 |

---

## Epic G-5 — Support and documentation

| ID | Task | Priority |
|----|------|----------|
| G-501 | Support runbook complete | P0 |
| G-502 | Repair/RMA workflow with hardware team | P1 |
| G-503 | Public release notes (GA channel) | P0 |
| G-504 | Claim boundary legal review | P1 |

---

## GA exit criteria

- [ ] All P0 tasks closed
- [ ] [../release_gates/GA_RELEASE_GATE.md](../release_gates/GA_RELEASE_GATE.md) evidence complete
- [ ] [../release_gates/RELEASE_SIGNOFF_TEMPLATE.md](../release_gates/RELEASE_SIGNOFF_TEMPLATE.md) signed
- [ ] No open P0 in [../release_gates/RELEASE_BLOCKERS.md](../release_gates/RELEASE_BLOCKERS.md) GA section

---

## Claim boundary

GA backlog completion enables **GA release** claims only after gate sign-off. Does **not** imply production fleet or finished shipping OS on unreleased SKUs.
