# Hardware Repo Source Map

Maps hardware industrial design artifacts to OS compatibility artifacts.

**Hardware repo root (relative from this repo):** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Product and architecture

| Hardware path | Content | OS consumer |
|---------------|---------|-------------|
| `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` | Modular console ecosystem PRD | All device profiles; `docs/DEVICE_SPECIFIC_OS_BEHAVIOR.md` |
| `product/PRODUCT_LINE_REQUIREMENTS.md` | Line-level requirements | `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md` |
| `product/PERFORMANCE_TARGETS.md` | Performance targets | `docs/HARDWARE_POWER_THERMAL_POLICY.md` |
| `product/EVT1_ACCEPTANCE_CRITERIA.md` | EVT1 acceptance | `docs/EVT1_OS_ACCEPTANCE_CRITERIA.md` (OS repo) |
| `product/CLAIM_BOUNDARY.md` | Hardware claims limit | `hardware_compat/HARDWARE_CLAIM_BOUNDARY.md` |
| `architecture/PRODUCT_LINE_ARCHITECTURE.md` | System architecture | `docs/HARDWARE_REPO_INTEGRATION.md` |
| `architecture/SYSTEM_BLOCK_DIAGRAM.md` | Block diagram | Boot and detection planning |
| `architecture/DEVICE_COMPARISON_MATRIX.md` | SKU comparison | `DEVICE_CLASS_COMPATIBILITY_MATRIX.md` |
| `architecture/POWER_TREE.md` | Power architecture | `docs/HARDWARE_POWER_THERMAL_POLICY.md` |
| `architecture/DATA_FLOW_AND_CONNECTOR_MAP.md` | Connectors | `docs/HARDWARE_STORAGE_NETWORK_POLICY.md` |
| `architecture/OS_HARDWARE_CONTRACT.md` | Architecture contract | `HARDWARE_COMPATIBILITY_CONTRACT.md` |
| `docs/OS_HARDWARE_CONTRACT.md` | OS-facing contract table | Profile `hardware_repo_source_paths`; `docs/HARDWARE_SOFTWARE_CONTRACT.md` |

---

## Mechanical correctness

| Hardware path | Content | OS consumer |
|---------------|---------|-------------|
| `mechanical_correctness/device_mechanical_targets.json` | Bbox, STL, expected class per SKU | `hardware_compat/device_profiles/*.yaml` |
| `mechanical_correctness/MECHANICAL_CORRECTNESS_REQUIREMENTS.md` | Requirements | Gap analysis |
| `mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md` | Gate status | `HARDWARE_VALIDATION_STATUS.md` |
| `mechanical_correctness/DISPLAY_FIT_CHECK_PLAN.md` | Display fit | `docs/HARDWARE_INPUT_DISPLAY_POLICY.md` |
| `mechanical_correctness/BUTTON_CONTROL_CLEARANCE_REQUIREMENTS.md` | Control clearance | Input policy docs |
| `mechanical_correctness/BATTERY_COMPARTMENT_FIT_CHECK.md` | Battery fit | Power/thermal policy |

---

## DVT (design validation test)

| Hardware path | Content | OS consumer |
|---------------|---------|-------------|
| `dvt/DVT_STATUS.md` | Overall DVT status | `HARDWARE_VALIDATION_STATUS.md` |
| `dvt/DVT_READINESS_REQUIREMENTS.md` | Readiness gates | `hardware_release/HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md` |
| `dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md` | SW/HW integration | `boot_readiness/DEVICE_BOOT_SEQUENCE.md` |
| `dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md` | Display/input tests | `docs/HARDWARE_INPUT_DISPLAY_POLICY.md` |
| `dvt/DVT_BATTERY_TEST_PLAN.md` | Battery tests | `docs/HARDWARE_POWER_THERMAL_POLICY.md` |
| `dvt/DVT_THERMAL_TEST_PLAN.md` | Thermal tests | `docs/HARDWARE_POWER_THERMAL_POLICY.md` |
| `dvt/DVT_ELECTRICAL_TEST_PLAN.md` | Electrical tests | Storage/network policy |
| `dvt/DVT_MECHANICAL_TEST_PLAN.md` | Mechanical tests | Mechanical gap analysis |

---

## PVT (production validation test)

| Hardware path | Content | OS consumer |
|---------------|---------|-------------|
| `pvt/PVT_STATUS.md` | PVT status | `hardware_release/HARDWARE_COMPATIBILITY_STATUS.md` |
| `pvt/PVT_READINESS_REQUIREMENTS.md` | Readiness | Release requirements |
| `pvt/PVT_PRODUCTION_TEST_PLAN.md` | Factory test plan | `hardware_release/HARDWARE_COMPATIBILITY_TEST_PLAN.md` |
| `pvt/PVT_FACTORY_PROCESS_PLAN.md` | Factory process | Pilot test plan |

---

## Certification

| Hardware path | Content | OS consumer |
|---------------|---------|-------------|
| `certification/CERTIFICATION_STATUS.md` | Cert status | `HARDWARE_VALIDATION_STATUS.md` |
| `certification/CERTIFICATION_READINESS_MATRIX.md` | Readiness matrix | Evidence matrix |
| `certification/CERTIFICATION_EVIDENCE_REQUIRED.md` | Required evidence | `HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` |
| `certification/FCC_CERTIFICATION_READINESS.md` | FCC | Release requirements |
| `certification/CE_UKCA_READINESS.md` | CE/UKCA | Release requirements |
| `certification/UN38_3_BATTERY_READINESS.md` | Battery shipping | Power policy / release |
| `certification/WIFI_BLUETOOTH_MODULE_CERT_READINESS.md` | Radio modules | Network policy |

---

## Production release

| Hardware path | Content | OS consumer |
|---------------|---------|-------------|
| `production_release/PRODUCTION_RELEASE_STATUS.md` | Release status | `hardware_release/HARDWARE_COMPATIBILITY_STATUS.md` |
| `production_release/PRODUCTION_RELEASE_REQUIREMENTS.md` | Requirements | `HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md` |
| `production_release/PRODUCTION_RELEASE_EVIDENCE_MATRIX.md` | Evidence | `HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` |
| `production_release/PRODUCTION_RELEASE_SIGNOFF_TEMPLATE.md` | Signoff | `HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md` |

---

## Per-SKU manufacturing packages

| Hardware path | OS profile |
|---------------|------------|
| `results/manufacturing/student_14_5_package_index.md` | `device_profiles/student_14_5.yaml` |
| `results/manufacturing/handheld_hybrid_package_index.md` | `device_profiles/handheld_hybrid.yaml` |
| `results/manufacturing/ds_xl_coder_package_index.md` | `device_profiles/ds_xl_coder.yaml` |
| `results/manufacturing/wearables_arena_set_package_index.md` | `device_profiles/wearables_arena_set.yaml` |

---

## OS profile → hardware anchor (quick reference)

| OS `device_id` | JSON key | Primary hardware sources |
|----------------|----------|--------------------------|
| `student_14_5` | `student_14` | `device_mechanical_targets.json`, `docs/OS_HARDWARE_CONTRACT.md`, PRD |
| `handheld_hybrid` | `handheld_hybrid` | same pattern |
| `ds_xl_coder` | `ds_xl_coder` | same pattern |
| `wearables_arena_set` | `wearables_arena_set` | same pattern |
