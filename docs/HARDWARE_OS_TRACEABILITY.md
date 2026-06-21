# Hardware / OS Traceability

**Status:** traceability matrix documented · **most evidence not_started**

Cross-reference between hardware repo artifacts and OS repo artifacts with compatibility implications and evidence status.

**Hardware repo:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Traceability matrix

| Hardware repo artifact | OS repo artifact | Compatibility implication | Evidence status |
|------------------------|------------------|---------------------------|-----------------|
| `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` | `hardware_compat/device_profiles/*.yaml` | Defines SKU capabilities OS must mirror | profile_mirror |
| `product/PRODUCT_LINE_REQUIREMENTS.md` | `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md` | Line requirements → OS gates | documented |
| `product/CLAIM_BOUNDARY.md` | `hardware_compat/HARDWARE_CLAIM_BOUNDARY.md` | Limits public hardware claims | documented |
| `architecture/PRODUCT_LINE_ARCHITECTURE.md` | `docs/DEVICE_ARCHITECTURE.md` | System context for boot/policy | documented |
| `architecture/DEVICE_COMPARISON_MATRIX.md` | `hardware_compat/DEVICE_CLASS_COMPATIBILITY_MATRIX.md` | SKU feature differences | profile_mirror |
| `architecture/POWER_TREE.md` | `docs/HARDWARE_POWER_THERMAL_POLICY.md` | Power/thermal assumptions | simulated |
| `architecture/DATA_FLOW_AND_CONNECTOR_MAP.md` | `docs/HARDWARE_STORAGE_NETWORK_POLICY.md` | Ports, storage, network | simulated |
| `architecture/OS_HARDWARE_CONTRACT.md` | `hardware_compat/HARDWARE_COMPATIBILITY_CONTRACT.md` | Architecture-level contract | documented |
| `docs/OS_HARDWARE_CONTRACT.md` | `docs/HARDWARE_SOFTWARE_CONTRACT.md` | Mode/input/dock/update obligations | documented |
| `mechanical_correctness/device_mechanical_targets.json` | `hardware_compat/device_profiles/*.yaml` | Mechanical class per SKU | profile_mirror |
| `mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md` | `hardware_compat/HARDWARE_VALIDATION_STATUS.md` | Mechanical gate blocks HW release | not_started |
| `mechanical_correctness/DISPLAY_FIT_CHECK_PLAN.md` | `docs/HARDWARE_INPUT_DISPLAY_POLICY.md` | Display fit → OS display policy | not_started |
| `dvt/DVT_STATUS.md` | `hardware_release/HARDWARE_COMPATIBILITY_STATUS.md` | DVT blocks R3 release | not_started |
| `dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md` | `boot_readiness/DEVICE_BOOT_SEQUENCE.md` | Boot/integration sequence | planned |
| `dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md` | `docs/HARDWARE_INPUT_DISPLAY_POLICY.md` | Input/display lab criteria | not_started |
| `dvt/DVT_BATTERY_TEST_PLAN.md` | `docs/HARDWARE_POWER_THERMAL_POLICY.md` | Battery runtime evidence | not_started |
| `dvt/DVT_THERMAL_TEST_PLAN.md` | `docs/HARDWARE_POWER_THERMAL_POLICY.md` | Thermal throttle evidence | not_started |
| `dvt/DVT_ELECTRICAL_TEST_PLAN.md` | `docs/HARDWARE_STORAGE_NETWORK_POLICY.md` | Storage/electrical qualification | not_started |
| `pvt/PVT_STATUS.md` | `hardware_release/HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md` | PVT required for R3 | not_started |
| `pvt/PVT_PRODUCTION_TEST_PLAN.md` | `hardware_release/HARDWARE_COMPATIBILITY_TEST_PLAN.md` | Factory test alignment | planned |
| `certification/CERTIFICATION_STATUS.md` | `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` | Regulatory rows | not_started |
| `certification/CERTIFICATION_EVIDENCE_REQUIRED.md` | `hardware_release/HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md` | Cert evidence list | documented |
| `production_release/PRODUCTION_RELEASE_STATUS.md` | `hardware_release/HARDWARE_COMPATIBILITY_STATUS.md` | Production gate | not_started |
| `production_release/PRODUCTION_RELEASE_EVIDENCE_MATRIX.md` | `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` | Shared evidence model | documented |
| `production_release/PRODUCTION_RELEASE_SIGNOFF_TEMPLATE.md` | `hardware_release/HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md` | Dual signoff | template_only |
| `results/manufacturing/student_14_5_package_index.md` | `docs/STUDENT_14_5_OS_BEHAVIOR.md` | Student SKU manufacturing ↔ OS behavior | profile_mirror |
| `results/manufacturing/handheld_hybrid_package_index.md` | `docs/HANDHELD_HYBRID_OS_BEHAVIOR.md` | Handheld manufacturing ↔ OS behavior | profile_mirror |
| `results/manufacturing/ds_xl_coder_package_index.md` | `docs/DS_XL_CODER_OS_BEHAVIOR.md` | DS-XL manufacturing ↔ OS behavior | profile_mirror |
| `results/manufacturing/wearables_arena_set_package_index.md` | `docs/WEARABLES_ARENA_OS_BEHAVIOR.md` | Wearables manufacturing ↔ OS behavior | profile_mirror |
| (hardware boot logs — future) | `gunnchos_device_os/hardware_boot_readiness.py` | Proves boot beyond simulation | not_started |
| (HLK reports — future) | `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` | Driver certification | not_started |

---

## Evidence status legend

| Status | Meaning |
|--------|---------|
| profile_mirror | OS YAML reflects hardware assumption; no silicon proof |
| documented | Cross-link or doc exists |
| simulated | Software-only check |
| planned | Plan written; execution pending |
| not_started | No execution evidence |
| validated | Lab/field evidence linked (**none in matrix above**) |
| template_only | Form exists; not filled |

---

## Maintenance

Update this matrix when:

- Hardware repo adds or renames artifacts under `product/`, `architecture/`, `dvt/`, `pvt/`, `certification/`, `production_release/`, `mechanical_correctness/`
- OS adds profiles, policies, or release evidence
- Evidence status advances after lab or pilot

---

## Claim boundary

Traceability proves **documentation alignment**, not hardware compatibility. Rows marked `profile_mirror`, `simulated`, `planned`, or `not_started` do not support hardware-compatible release claims.

See [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md).

---

## Related documents

- [HARDWARE_REPO_INTEGRATION.md](HARDWARE_REPO_INTEGRATION.md)
- [HARDWARE_REPO_COMPATIBILITY_AUDIT.md](HARDWARE_REPO_COMPATIBILITY_AUDIT.md)
- [../hardware_compat/HARDWARE_REPO_SOURCE_MAP.md](../hardware_compat/HARDWARE_REPO_SOURCE_MAP.md)
