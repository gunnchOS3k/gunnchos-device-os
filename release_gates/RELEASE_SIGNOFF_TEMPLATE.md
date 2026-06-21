# Release Sign-Off Template

**Version:** 1.0 · Copy per release · **Do not sign GA without artifacts**

---

## Release metadata

| Field | Value |
|-------|-------|
| Release version | |
| Gate | alpha / beta / release_candidate / ga_release / field_pilot / production_release |
| Build ID | |
| Channel | stable / beta / dev / school_managed |
| Supported SKUs | student_14_5 / handheld_hybrid / ds_xl_coder / wearables_arena_set |
| Sign-off date | |
| Release owner | |

---

## Evidence checklist

| # | Evidence item | Artifact hash / link | Verified by | Date |
|---|---------------|---------------------|-------------|------|
| 1 | pytest + validators green | CI run URL | | |
| 2 | Demo outputs generated | `results/` hashes | | |
| 3 | Signed bundle (if RC+) | | | |
| 4 | Checksums verified | | | |
| 5 | SBOM published (if RC+) | | | |
| 6 | Security review (if RC+) | | | |
| 7 | UAT report (if RC+) | | | |
| 8 | Accessibility report (if RC+) | | | |
| 9 | Hardware compatibility (if GA) | | | |
| 10 | Claim boundary reviewed | [../requirements/CLAIM_BOUNDARY.md](../requirements/CLAIM_BOUNDARY.md) | | |

---

## Risk waivers

| Risk ID | Description | Waiver approver | Expiry |
|---------|-------------|-----------------|--------|
| | | | |

---

## Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Release owner | | | |
| QA lead | | | |
| Security (RC+) | | | |
| Program (GA+) | | | |

---

## Allowed claims for this release

(List only claims permitted for this gate — see [../requirements/SHIPPABLE_OS_REQUIREMENTS.md](../requirements/SHIPPABLE_OS_REQUIREMENTS.md))

---

## Explicit non-claims

- Finished shipping OS (unless production gate with evidence)
- GA release (unless ga_release gate passed)
- Accessibility certified on hardware (unless report attached)
- Production MDM deployed (unless integration evidence)
- Secure boot complete on all devices (unless per-SKU reports)

---

## Notes
