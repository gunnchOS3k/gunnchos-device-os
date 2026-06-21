# Shippable OS Roadmap

**Last updated:** 2026-06-21 · **not shipping yet**

---

## Current state (honest)

| Milestone | Status |
|-----------|--------|
| User-focused OS alpha | **Done** — demos, launcher mock, pytest |
| Issue backlog OS alpha | **Done** — modules #1, #2, #3, #5, #7, #8, #9, #10, #12 |
| Shippable requirements package | **Done** — this documentation pass |
| Beta (installer prototype) | **not_started** |
| Release candidate | **not_started** |
| GA release | **not met** |
| Field pilot | **not_started** |
| Production release | **not_started** |

---

## Roadmap phases

```text
2026 Q2-Q3          2026 Q3-Q4           2027 Q1              2027+
─────────────────────────────────────────────────────────────────────
Alpha (now)    →    Beta            →    Release Candidate  →   GA
requirements        installer proto       signed bundle          HW validation
+ CI fix            launcher e2e          SBOM/checksums         UAT + support
                    mode e2e              recovery demo          performance
                                                              → Field Pilot
                                                              → Production
```

---

## Phase deliverables

### Phase 1 — Alpha (current)

- [x] Config-driven OS framework
- [x] User-focused 11-scenario demo
- [x] Shippable requirements, gates, QA, roadmap docs
- [x] CI validators for package integrity
- [ ] CI demo self-generation (branch in progress)

### Phase 2 — Beta

See [RELEASE_CANDIDATE_BACKLOG.md](RELEASE_CANDIDATE_BACKLOG.md) items 1–7 as prerequisites.

- Internal installer prototype
- Version manifest draft
- Launcher e2e smoke tests

### Phase 3 — Release candidate

Full [RELEASE_CANDIDATE_BACKLOG.md](RELEASE_CANDIDATE_BACKLOG.md) (20 tasks).

- Signed bundle + recovery
- Hardware compatibility matrix validation (automated cross-check)
- Security review checklist
- UAT + accessibility report generator

### Phase 4 — GA release

See [GA_RELEASE_BACKLOG.md](GA_RELEASE_BACKLOG.md).

- Hardware validation per SKU
- Performance/battery baselines
- Support runbooks
- GA sign-off

### Phase 5 — Field pilot & production

See [PRODUCTION_RELEASE_BACKLOG.md](PRODUCTION_RELEASE_BACKLOG.md).

- Pilot enrollment + field support
- Fleet update channel
- Production signing + rollback drill

---

## Engineering milestones

Detailed timeline: [ENGINEERING_MILESTONES.md](ENGINEERING_MILESTONES.md)

---

## Dependencies and risks

[DEPENDENCY_AND_RISK_REGISTER.md](DEPENDENCY_AND_RISK_REGISTER.md)

---

## Success criteria (shippable OS)

A shippable OS release is achieved when:

1. GA release gate **passed** with signed artifacts
2. Installable image proven on all GA SKUs in compatibility matrix
3. Update + rollback drill evidence archived
4. UAT + accessibility validation reports filed
5. Claim boundary reviewed — no over-claiming

**Today:** criteria 1–5 are **not met**.

---

## Related documents

- [../requirements/SHIPPABLE_OS_REQUIREMENTS.md](../requirements/SHIPPABLE_OS_REQUIREMENTS.md)
- [../release_gates/RELEASE_GATE_MATRIX.md](../release_gates/RELEASE_GATE_MATRIX.md)
- [../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md](../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md)
