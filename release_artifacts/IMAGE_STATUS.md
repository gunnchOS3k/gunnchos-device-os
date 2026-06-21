# Image Status

**Status:** `not_started` · installable image **not proven**

---

## Summary

| Image type | Status | Evidence |
|------------|--------|----------|
| gunnchOS OS-layer package | **not built** | — |
| Recovery image / bundle | **not built** | — |
| Factory restore image | **not built** | — |
| Bare-metal OS image (future) | **not in scope for alpha** | Hardware program TBD |

---

## What exists instead (alpha)

- Config-driven software framework in Python
- Launcher mock (web dev server)
- Deploy offline bundle **contract** (not production image)

---

## Validation path (planned)

1. Build OS-layer bundle in CI
2. Install on Student 14.5 reference PC
3. Boot launcher + mode switch smoke
4. Recovery menu drill
5. Document in hardware compatibility report

---

## Requirements reference

- [../requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md](../requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md)
- [../requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md](../requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md)

---

## Claim boundary

Installable image has **not** been validated on hardware. Do not claim finished shipping OS image or GA-ready image.
