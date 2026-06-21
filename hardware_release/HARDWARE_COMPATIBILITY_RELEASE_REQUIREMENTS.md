# Hardware Compatibility Release Requirements

**Status:** requirements defined · **hardware-compatible release not met**

**Note:** All current hardware compatibility is simulated/profile-based. Real hardware validation is required before hardware-compatible release can be claimed.

---

## Release tiers

| Tier | Name | May claim |
|------|------|-----------|
| R0 | Profile mirror release | Documentation + YAML profiles aligned with hardware repo |
| R1 | Simulated compatibility release | Policy engine + simulated boot pass in CI |
| R2 | Lab-validated compatibility | DVT-linked evidence per SKU |
| R3 | Hardware-compatible product release | DVT + cert + PVT + production gates |

**Current tier: R1** (simulated only)

---

## R2 minimum requirements (per SKU)

| ID | Requirement | Hardware source |
|----|-------------|-----------------|
| HCR-001 | Mechanical target documented | `mechanical_correctness/device_mechanical_targets.json` |
| HCR-002 | OS profile cites hardware sources | `hardware_compat/device_profiles/*.yaml` |
| HCR-003 | Boot to shell on reference unit | OS + `dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md` |
| HCR-004 | Display/input DVT pass | `dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md` |
| HCR-005 | Battery DVT pass (if applicable) | `dvt/DVT_BATTERY_TEST_PLAN.md` |
| HCR-006 | Thermal DVT pass | `dvt/DVT_THERMAL_TEST_PLAN.md` |
| HCR-007 | Storage qualification | `dvt/DVT_ELECTRICAL_TEST_PLAN.md` |
| HCR-008 | Recovery image tested | `boot_readiness/SAFE_MODE_AND_RECOVERY_PLAN.md` |
| HCR-009 | Mode matrix spot-check on hardware | OS compatibility test plan |
| HCR-010 | Known gaps closed or waived with signoff | gap analysis |

---

## R3 additional requirements (product release)

| ID | Requirement | Hardware source |
|----|-------------|-----------------|
| HCR-011 | DVT complete with signoff | `dvt/DVT_STATUS.md` |
| HCR-012 | PVT complete | `pvt/PVT_STATUS.md` |
| HCR-013 | Regulatory evidence | `certification/CERTIFICATION_EVIDENCE_REQUIRED.md` |
| HCR-014 | Production release gate | `production_release/PRODUCTION_RELEASE_REQUIREMENTS.md` |
| HCR-015 | HLK or driver certification | OS lab / Microsoft HLK |
| HCR-016 | Field pilot pass | `HARDWARE_PILOT_TEST_PLAN.md` |
| HCR-017 | Release signoff | `HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md` |

---

## Cross-repo obligations

### Hardware repo must provide

- Executed DVT/PVT reports (not just plans)
- Certification lab artifacts when claiming R3
- Locked BOM / flash layout for secure update
- Factory test procedures per SKU

### OS repo must provide

- Evidence matrix updates with artifact links
- Boot and compatibility test logs
- Honest release notes without overclaim
- Traceability in `docs/HARDWARE_OS_TRACEABILITY.md`

---

## Product PRD alignment

`../gunnchos-hardware-industrial-design/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md`  
`../gunnchos-hardware-industrial-design/product/PRODUCT_LINE_REQUIREMENTS.md`

---

## Explicit non-requirements for R1 (current)

- Physical boot proof
- HLK certification
- FCC/CE labels
- Production CM signoff

---

## Related documents

- [HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md](HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md)
- [HARDWARE_COMPATIBILITY_STATUS.md](HARDWARE_COMPATIBILITY_STATUS.md)
- [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md)
