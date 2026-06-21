# Release Candidate Gate

**Gate ID:** `release_candidate` · **Status:** `not_started`

---

## Purpose

First gate allowing **release candidate** language for field evaluation on an approved device list — not general sale or GA.

---

## Entry criteria

- Beta gate passed (or waived with documented risk)
- Security review checklist complete
- All RC artifacts in [../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md](../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md)

---

## Required evidence

| Artifact | Status |
|----------|--------|
| Signed OS-layer installer/bundle | not_started |
| Checksums + signed manifest | not_started |
| SBOM | not_started |
| Recovery bundle | not_started |
| Release notes | template only |
| Hardware compatibility report (draft) | not_started |
| Accessibility report (draft) | not_started |
| Security review report | in_progress |
| UAT report | not_started |
| RC sign-off | not_started |

---

## Required tests

Full RC suite per [../requirements/RELEASE_CANDIDATE_REQUIREMENTS.md](../requirements/RELEASE_CANDIDATE_REQUIREMENTS.md).

---

## Allowed claims

- Release candidate for field evaluation
- Not for general public sale

---

## Forbidden claims

- GA release
- Production MDM deployed
- Accessibility certified on hardware
- Finished shipping OS

---

## Owner

Release engineering + QA lead
