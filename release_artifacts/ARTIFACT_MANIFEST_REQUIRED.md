# Artifact Manifest — Required

**Last updated:** 2026-06-21 · honest inventory

---

## Current alpha artifacts

These exist in the repository today. They support **alpha** claims only.

| Artifact | Location | Purpose |
|----------|----------|---------|
| User-focused OS modules | `gunnchos_device_os/` | Policy, modes, deploy, guardian, privacy |
| YAML configs | `config/` | Device classes, modes, deploy targets, guardian, privacy |
| Demo scripts | `scripts/run_*_demo.py` | Reproducible evidence JSON |
| Demo outputs | `results/*_demo_output.json` | CI-validated scenarios |
| Launcher mock | `apps/launcher_mock/` | UX prototype |
| Architecture docs | `docs/` | Contracts and walkthroughs |
| pytest suite | `tests/` | Automated validation |
| Diagrams | `diagrams/` | Deploy flow mermaid |
| Shippable requirements package | `requirements/`, `release_gates/`, `qa/`, `roadmap/` | Release track definition |

**Not included in alpha as shipping artifacts:** installer, signed bundle, SBOM, recovery image, hardware test reports.

---

## Required before release candidate

These must exist before RC gate may be marked `passed`. **None are complete today.**

| Artifact | Requirement | Status |
|----------|-------------|--------|
| Installer | Windows-first gunnchOS shell installer (signed) | **not_started** |
| Versioned release bundle | Immutable bundle ID + semver | **planned** |
| Signed manifest | Signature over file list + hashes | **planned** |
| Checksums file | SHA-256 per artifact | **not_started** |
| SBOM | SPDX or CycloneDX for bundle | **not_started** |
| Recovery bundle | Offline recovery package | **not_started** |
| Release notes | User + operator (from template) | template only |
| Hardware compatibility report | Per-SKU matrix with test logs | **not_started** |
| Accessibility report | Manual validation log (not certification) | **not_started** |
| Security review report | Completed checklist | **in_progress** |
| User acceptance report | UAT execution vs RC build | **not_started** |

---

## Required before GA (increment over RC)

| Artifact | Status |
|----------|--------|
| GA-signed installer | not_started |
| Published SBOM archive | not_started |
| Final UAT report | not_started |
| Accessibility validation report (hardware) | not_started |
| Support runbooks | partial |
| Signed compatibility matrix | not_started |

---

## Verification

Do not list RC artifacts as "available" until build pipeline produces them and checksums are verified. See status docs:

- [BUILD_ARTIFACTS_STATUS.md](BUILD_ARTIFACTS_STATUS.md)
- [INSTALLER_STATUS.md](INSTALLER_STATUS.md)
- [IMAGE_STATUS.md](IMAGE_STATUS.md)
- [CHECKSUMS_STATUS.md](CHECKSUMS_STATUS.md)

---

## Claim boundary

Current alpha artifacts do **not** constitute a shippable release bundle. Required before release candidate items are **not yet built** — do not claim otherwise.
