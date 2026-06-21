# Claim Boundary — Shippable OS

**Effective:** 2026-06-21 · applies to all requirements, gates, QA, and roadmap docs

This document does not claim finished shipping, certification, secure boot, or production MDM without evidence.

---

## What this repo is today

- User-focused **OS alpha** and launcher/customization framework
- Config-driven device classes, modes, deploy contracts, guardian/privacy models
- Launcher mock (fleet + user-focused views)
- Demo scripts producing JSON evidence
- pytest suite and CI validators

---

## Allowed language (without extra evidence)

- shippable OS **requirements**
- release-candidate **gate** / production-readiness **track**
- installable image **requirement**
- signed update **requirement**
- recovery **requirement**
- hardware compatibility **requirement**
- privacy/security **baseline**
- accessibility **validation track**
- **not shipping yet**
- **release evidence required**
- user-focused OS alpha exists
- issue backlog OS alpha exists

---

## Forbidden language (unless linked evidence exists)

| Forbidden claim | Required evidence to allow |
|-----------------|---------------------------|
| Finished shipping OS / production OS | GA gate passed + installable image validated on hardware |
| Certified OS / COPPA-GDPR certified | Legal review + compliance audit report |
| Secure boot complete on all devices | Per-SKU secure boot test report |
| Production MDM deployed | MDM integration test report + fleet config |
| Accessibility certified on hardware | Accessibility validation report with hardware test log |
| Official Steam / media certification | Partner certification documents |
| Hardware-validated release | Hardware compatibility report per SKU |
| Production fleet management | Production release gate + fleet ops runbook |

---

## Document rules

1. Requirements docs describe **targets**, not shipped reality.
2. Status tables must use honest states: `not_started`, `planned`, `in_progress`, `evidence_exists`, `validated`, `blocked` — not `passed` for GA without artifacts.
3. Forbidden phrases may appear only when negated (e.g., "does not claim", "not yet", "not claimed").
4. Alpha artifacts must not be listed as RC/GA artifacts without a build pipeline.

---

## Cross-references

- [../release_gates/RELEASE_GATE_MATRIX.md](../release_gates/RELEASE_GATE_MATRIX.md)
- [../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md](../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md)
- [../docs/WHAT_IS_REAL_TODAY.md](../docs/WHAT_IS_REAL_TODAY.md)
- [../product/CLAIM_BOUNDARY.md](../product/CLAIM_BOUNDARY.md)
