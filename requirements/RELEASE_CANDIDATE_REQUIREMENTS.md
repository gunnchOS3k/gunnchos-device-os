# Release Candidate Requirements

**Stage:** `release_candidate` · **Status:** not met · release evidence required

> RC is the first stage where a signed, installable bundle may be evaluated on approved hardware. This repo does not claim RC status today. This document does not claim secure boot, production MDM, or finished shipping without evidence.

---

## Entry criteria (from beta)

- [ ] Internal installer prototype exercised on at least one reference device
- [ ] Version manifest and checksum pipeline automated
- [ ] Launcher e2e smoke tests green
- [ ] No open P0 defects in release blockers register

---

## Required artifacts

| Artifact | Description | Current status |
|----------|-------------|----------------|
| Signed OS-layer installer | Windows-first gunnchOS shell installer | **not_started** |
| Versioned release bundle | Immutable bundle ID + semantic version | **planned** |
| Signed manifest | Cryptographic manifest over bundle contents | **planned** |
| Checksums file | SHA-256 per artifact | **planned** |
| SBOM | SPDX or CycloneDX for release contents | **planned** |
| Recovery bundle | Offline recovery / factory reset package | **planned** |
| Release notes | User-facing + operator-facing | template exists |
| Hardware compatibility report | Per-SKU matrix with pass/fail | **not_started** |
| Accessibility report | Manual validation log (not certification) | **not_started** |
| Security review report | Checklist + threat model delta | **in_progress** (partial threat model) |
| User acceptance report | UAT execution against RC build | **not_started** |

See [../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md](../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md).

---

## Required tests

| Domain | Plan | Minimum bar |
|--------|------|-------------|
| Regression | [../qa/REGRESSION_TEST_PLAN.md](../qa/REGRESSION_TEST_PLAN.md) | 100% P0/P1 automated cases pass |
| UAT | [../qa/USER_ACCEPTANCE_TEST_PLAN.md](../qa/USER_ACCEPTANCE_TEST_PLAN.md) | All RC scenarios pass on 2+ personas |
| Accessibility | [../qa/ACCESSIBILITY_TEST_PLAN.md](../qa/ACCESSIBILITY_TEST_PLAN.md) | No P0 a11y blockers; report filed |
| Guardian | [../qa/GUARDIAN_CONTROLS_TEST_PLAN.md](../qa/GUARDIAN_CONTROLS_TEST_PLAN.md) | Approval + audit log scenarios pass |
| School/library | [../qa/SCHOOL_LIBRARY_TEST_PLAN.md](../qa/SCHOOL_LIBRARY_TEST_PLAN.md) | Session cleanup verified |
| Offline | [../qa/OFFLINE_MODE_TEST_PLAN.md](../qa/OFFLINE_MODE_TEST_PLAN.md) | Offline bundle install + launch |
| Performance | [../qa/PERFORMANCE_TEST_PLAN.md](../qa/PERFORMANCE_TEST_PLAN.md) | Baselines recorded (not GA-tuned) |

---

## Required evidence

1. Completed [../release_gates/RELEASE_SIGNOFF_TEMPLATE.md](../release_gates/RELEASE_SIGNOFF_TEMPLATE.md) for RC
2. [../release_gates/RELEASE_EVIDENCE_MATRIX.md](../release_gates/RELEASE_EVIDENCE_MATRIX.md) rows populated for RC scope
3. CI artifacts: pytest + all validators green on RC tag
4. Stored build logs and checksum verification log
5. RC release notes published alongside bundle (internal channel)

---

## Allowed claims at RC

- "Release candidate for field evaluation on approved device list"
- "Known issues documented; not for general public sale"
- "Accessibility validation in progress — not certified"

---

## Forbidden claims at RC

- GA release or production OS
- Accessibility certified on hardware
- Secure boot complete on all devices
- Production MDM deployed
- Finished shipping OS image

---

## Exit criteria (to GA)

All [GA_RELEASE_REQUIREMENTS.md](GA_RELEASE_REQUIREMENTS.md) met, GA gate passed, claim boundary re-reviewed.
