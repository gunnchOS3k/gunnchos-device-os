# Hardware Compatibility Evidence Matrix

**Status:** All current hardware compatibility is simulated/profile-based. Real hardware validation is required before hardware-compatible release can be claimed.

Last updated: 2026-06-21

---

## Matrix

| Device class | Required evidence | Current evidence | Status | Blocking? |
|--------------|-------------------|------------------|--------|-----------|
| Student 14.5 | YAML profile + hardware source paths | `hardware_compat/device_profiles/student_14_5.yaml`; mechanical JSON cite | profile_mirror | no (R0/R1) |
| Student 14.5 | Simulated boot readiness pass | `hardware_boot_readiness.py` API | simulated | no (R1) |
| Student 14.5 | Reference hardware boot log | none | not_started | **yes** (R2+) |
| Student 14.5 | DVT display/input report | hardware plan only (`dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md`) | not_started | **yes** (R2+) |
| Student 14.5 | DVT battery report | hardware plan only (`dvt/DVT_BATTERY_TEST_PLAN.md`) | not_started | **yes** (R2+) |
| Student 14.5 | DVT thermal report | hardware plan only (`dvt/DVT_THERMAL_TEST_PLAN.md`) | not_started | **yes** (R2+) |
| Student 14.5 | HLK / driver certification | none | not_started | **yes** (R3) |
| Student 14.5 | USB recovery boot test | none | not_started | **yes** (R2+) |
| Handheld Hybrid | YAML profile + hardware source paths | `handheld_hybrid.yaml` | profile_mirror | no (R0/R1) |
| Handheld Hybrid | Simulated boot readiness pass | API simulated | simulated | no (R1) |
| Handheld Hybrid | Controller mapping on hardware | none | not_started | **yes** (R2+) |
| Handheld Hybrid | TV/dock display validation | none | not_started | **yes** (R2+) |
| Handheld Hybrid | Gaming thermal/battery logs | none | not_started | **yes** (R2+) |
| Handheld Hybrid | Steam compatibility evidence | known gap | not_started | **yes** (R3 marketing) |
| DS-XL Coder | YAML profile + hardware source paths | `ds_xl_coder.yaml` | profile_mirror | no (R0/R1) |
| DS-XL Coder | Simulated boot readiness pass | API simulated | simulated | no (R1) |
| DS-XL Coder | Dual-screen boot/init log | none | not_started | **yes** (R2+) |
| DS-XL Coder | Deploy transport E2E on hardware | mock API only | not_started | **yes** (R2+) |
| DS-XL Coder | Developer thermal under load | none | not_started | **yes** (R2+) |
| Wearables / Arena | YAML profile + hardware source paths | `wearables_arena_set.yaml` | profile_mirror | no (R0/R1) |
| Wearables / Arena | Simulated boot readiness pass | API simulated | simulated | no (R1) |
| Wearables / Arena | Arena marshal field pilot | none | not_started | **yes** (R2+) |
| Wearables / Arena | Haptic/safety validation | none | not_started | **yes** (R2+) |
| All SKUs | DVT complete signoff | `dvt/DVT_STATUS.md`: not complete | not_started | **yes** (R3) |
| All SKUs | PVT complete signoff | `pvt/PVT_STATUS.md`: not complete | not_started | **yes** (R3) |
| All SKUs | FCC/CE/UKCA certification | `certification/CERTIFICATION_STATUS.md`: not certified | not_started | **yes** (R3) |
| All SKUs | Production release gate | `production_release/PRODUCTION_RELEASE_STATUS.md`: not released | not_started | **yes** (R3) |

---

## Status legend

| Status | Meaning |
|--------|---------|
| profile_mirror | YAML aligned with hardware repo assumptions |
| simulated | Software-only check passed |
| not_started | No linked execution evidence |
| validated | Lab/field evidence linked (**none today**) |
| blocked | Dependency prevents progress |

---

## Evidence artifact locations (when available)

| Type | Expected location |
|------|-------------------|
| OS boot logs | `results/hardware_boot/` (future) |
| DVT reports | hardware repo `dvt/` report templates filled |
| Cert reports | hardware repo `certification/` |
| Pilot reports | `results/field_pilot/` (future) |
| Signoff | `hardware_release/signoffs/` (future) |

---

## Update protocol

1. Execute test from [HARDWARE_COMPATIBILITY_TEST_PLAN.md](HARDWARE_COMPATIBILITY_TEST_PLAN.md)
2. Store artifact with checksum
3. Update row: Current evidence, Status, Blocking?
4. Cross-link in [../docs/HARDWARE_OS_TRACEABILITY.md](../docs/HARDWARE_OS_TRACEABILITY.md)
5. Re-evaluate [HARDWARE_COMPATIBILITY_STATUS.md](HARDWARE_COMPATIBILITY_STATUS.md)

---

## Claim boundary

Rows marked `simulated` or `profile_mirror` do **not** satisfy hardware-compatible release. Blocking? **yes** rows must clear before R2/R3 claims.
