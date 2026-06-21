# GA Release Requirements

**Stage:** `ga_release` · **Status:** **not met** · release evidence required

> GA (generally available) is the first stage where public claims of a supported gunnchOS release are permitted for hardware listed in the compatibility matrix. GA release is not claimed today. This document does not claim production MDM deployed without integration evidence.

---

## Prerequisites

- Release candidate gate **passed** with no waivers on security, recovery, or signing
- All P0/P1 defects closed or formally waived with expiry
- Support and repair runbooks published
- Claim boundary reviewed by release owner

---

## Required artifacts (GA increment over RC)

| Artifact | Requirement |
|----------|-------------|
| GA-signed installer | Production or GA signing key; key ceremony documented |
| Published SBOM | Archived per release tag |
| Final UAT report | All GA personas and device classes in matrix |
| Accessibility validation report | Hardware-tested; **does not claim** third-party certification unless audit attached |
| Security review sign-off | Threat model current; dependency review complete |
| Support runbook | Tier-1 troubleshooting, reset, rollback |
| Repair workflow doc | RMA / parts path linked from [SUPPORT_AND_REPAIR_REQUIREMENTS.md](SUPPORT_AND_REPAIR_REQUIREMENTS.md) |
| Compatibility matrix (final) | student_14_5, handheld_hybrid, ds_xl_coder — wearables per pilot waiver |

---

## Required tests

| Test area | Pass criteria |
|-----------|---------------|
| Full regression | Automated + manual GA suite; 0 open P0 |
| Performance | Meets documented baselines per SKU |
| Battery / thermal | Handoff complete per [../qa/BATTERY_THERMAL_TEST_HANDOFF.md](../qa/BATTERY_THERMAL_TEST_HANDOFF.md) |
| Update / rollback | Staged update + rollback drill on each supported SKU |
| Recovery | Factory reset + last-known-good exercised |
| Guardian / youth | All GA scenarios in guardian test plan |
| Offline-first | 72-hour offline operation scenario |

---

## Required evidence

1. [../release_gates/GA_RELEASE_GATE.md](../release_gates/GA_RELEASE_GATE.md) status = `passed` (only after artifacts exist)
2. Evidence matrix rows for GA populated with artifact hashes
3. 30-day post-RC soak notes (if applicable)
4. Published release notes (public channel)
5. Security disclosure policy link live

---

## Allowed claims at GA

- "Generally available gunnchOS release for [supported SKU list]"
- "Documented update and rollback policy"
- "Accessibility validation report available" (not "certified" unless audit attached)

---

## Forbidden claims at GA (without additional gates)

- Production fleet management / nationwide rollout
- Secure boot complete on **all** devices including future SKUs
- Production MDM deployed
- Official Steam or media partner certification
- Finished shipping OS on unreleased hardware

---

## Current honest status

| Item | Status |
|------|--------|
| GA gate | **not_started** |
| Installable image proven | **no** |
| Hardware validation | **not physically proven** |
| Security review complete | **no** |
| Accessibility certified | **not claimed** |

See [../release_gates/RELEASE_GATE_MATRIX.md](../release_gates/RELEASE_GATE_MATRIX.md).
