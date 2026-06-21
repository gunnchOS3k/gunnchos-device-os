# GA Release Gate

**Gate ID:** `ga_release` · **Status:** `not_started` · **GA release not met**

---

## Purpose

Generally available gunnchOS for hardware in the compatibility matrix — with support, signing, and validation evidence.

---

## Entry criteria

- Release candidate gate **passed**
- Zero open P0 defects (or formal waiver with expiry)
- Claim boundary re-reviewed

---

## Required evidence

| Item | Status |
|------|--------|
| GA-signed installer | not_started |
| Published SBOM archive | not_started |
| Final UAT report (all GA personas + SKUs) | not_started |
| Accessibility validation report (hardware) | not_started |
| Security review sign-off | not_started |
| Support + repair runbooks | partial docs |
| Compatibility matrix (signed) | not_started |
| GA sign-off template | not_started |

---

## Required tests

- GA regression per [../requirements/GA_RELEASE_REQUIREMENTS.md](../requirements/GA_RELEASE_REQUIREMENTS.md)
- Update + rollback drill per SKU
- Performance and battery/thermal baselines

---

## Allowed claims (only when gate passed)

- Generally available gunnchOS for [listed SKUs]
- Documented update/rollback policy

---

## Forbidden claims (without production gate)

- Production fleet management
- Secure boot complete on all future SKUs
- Finished shipping OS image is complete everywhere

---

## Current honest assessment

**GA release is not met.** Installable image is not yet proven. Do not mark this gate `passed` until artifacts exist.

---

## Owner

Release program manager
