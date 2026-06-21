# Installable Image Requirements

**Status:** requirements only · installable image **not yet proven**

> Defines what a shippable gunnchOS installable image or OS-layer package must include. This document does not claim a finished shipping os image is complete or that installable artifacts exist in production builds today.

---

## Scope

gunnchOS ships as a **Windows-first OS-layer** (shell, launcher, policies, recovery hooks) with optional portable/offline installers. A future bare-metal image path may be added per hardware program; requirements below apply to the OS-layer package unless noted.

---

## Required package components

| Component | Requirement | Current status |
|-----------|-------------|----------------|
| Windows-first gunnchOS shell installer | MSI/EXE or signed script bundle; silent + interactive modes | **not_started** |
| Launcher package | Versioned launcher binary or packaged web shell | launcher mock only |
| Recovery package | Offline recovery launcher + reset hooks | **planned** |
| Portable offline installer | USB/offline bundle for school/library | deploy offline bundle contract only |
| Version manifest | Semantic version, build ID, channel, SKU list | template in release_artifacts |
| Checksum/hash file | SHA-256 per file + manifest signature | **not_started** |
| Release notes | User + operator sections | template exists |
| Upgrade path | In-place upgrade preserving profiles | design in updater mock |
| Uninstall/reset path | Remove OS-layer; optional profile wipe | **planned** |
| Factory restore path | Restore to shipped image state | **planned** |

---

## Functional requirements

### Installation

1. Installer verifies minimum Windows version and supported SKU (when hardware ID available).
2. First-run wizard launches after install (see [USER_EXPERIENCE_REQUIREMENTS.md](USER_EXPERIENCE_REQUIREMENTS.md)).
3. Install logs written locally; no silent failure.
4. Disk space pre-check with human-readable error.

### Versioning

- Semantic versioning: `MAJOR.MINOR.PATCH` + build metadata
- Channel tag: `stable`, `beta`, `dev`, `school_managed`
- Manifest must list bundled config hashes

### Integrity

- All release artifacts covered by signed manifest (see [../release_artifacts/SIGNING_REQUIREMENTS.md](../release_artifacts/SIGNING_REQUIREMENTS.md))
- Checksum verification step before apply (installer self-check)

### Upgrade & uninstall

- Upgrade preserves user profiles unless breaking change documented
- Uninstall removes OS-layer; does not claim to remove Windows or third-party apps
- Reset offers: keep files / remove profiles / factory restore

---

## Evidence required before RC

| Evidence | Owner |
|----------|-------|
| Build pipeline log producing versioned bundle | Release engineering |
| Checksum verification log | Release engineering |
| Install/uninstall test report on reference PC | QA |
| Upgrade test report (N-1 → N) | QA |

---

## Claim boundary

This document defines installable image **requirements**. It does **not** claim an installable image has been validated on hardware or that a finished shipping OS image is complete.
