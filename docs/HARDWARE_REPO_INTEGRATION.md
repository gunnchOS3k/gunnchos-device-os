# Hardware Repo Integration

**Status:** integration documented · **physical validation not proven**

Describes how `gunnchos-device-os` integrates with the hardware industrial design repository at [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design).

---

## Repository relationship

```
gunnchos-hardware-industrial-design          gunnchos-device-os
├── product/PRD                              ├── hardware_compat/device_profiles/
├── architecture/                            ├── gunnchos_device_os/hardware_*.py
├── docs/OS_HARDWARE_CONTRACT.md  ←──────→  ├── docs/HARDWARE_SOFTWARE_CONTRACT.md
├── mechanical_correctness/                  ├── boot_readiness/
│   └── device_mechanical_targets.json       ├── hardware_release/
├── dvt/                                     └── docs/HARDWARE_OS_TRACEABILITY.md
├── pvt/
├── certification/
└── production_release/
```

Hardware owns physical design, DVT/PVT, certification, and production release. OS owns profile mirror, policy enforcement, simulated boot, and release evidence scaffolding.

---

## Integration surfaces

### 1. Product and requirements

| Hardware | OS |
|----------|-----|
| `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` | Device behavior docs, profiles |
| `product/PRODUCT_LINE_REQUIREMENTS.md` | `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md` |
| `product/CLAIM_BOUNDARY.md` | `hardware_compat/HARDWARE_CLAIM_BOUNDARY.md` |

### 2. Architecture and contract

| Hardware | OS |
|----------|-----|
| `architecture/PRODUCT_LINE_ARCHITECTURE.md` | `docs/DEVICE_ARCHITECTURE.md` |
| `architecture/DEVICE_COMPARISON_MATRIX.md` | `hardware_compat/DEVICE_CLASS_COMPATIBILITY_MATRIX.md` |
| `architecture/OS_HARDWARE_CONTRACT.md` | `hardware_compat/HARDWARE_COMPATIBILITY_CONTRACT.md` |
| `docs/OS_HARDWARE_CONTRACT.md` | `docs/HARDWARE_SOFTWARE_CONTRACT.md` |

### 3. Mechanical correctness

| Hardware | OS |
|----------|-----|
| `mechanical_correctness/device_mechanical_targets.json` | Profile `hardware_repo_source_paths` |
| `mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md` | Gap analysis, validation status |

### 4. Validation lifecycle

| Hardware stage | OS consumer |
|----------------|-------------|
| `dvt/` | `boot_readiness/`, `hardware_release/HARDWARE_COMPATIBILITY_TEST_PLAN.md` |
| `pvt/` | Release requirements R3 |
| `certification/` | Evidence matrix regulatory rows |
| `production_release/` | Release signoff template |

---

## Device ID mapping

| Hardware JSON key | OS `device_id` | Manufacturing path |
|-------------------|------------------|--------------------|
| `student_14` | `student_14_5` | `manufacturing/student_14_5/` |
| `handheld_hybrid` | `handheld_hybrid` | `manufacturing/handheld_hybrid/` |
| `ds_xl_coder` | `ds_xl_coder` | `manufacturing/ds_xl_coder/` |
| `wearables_arena_set` | `wearables_arena_set` | `manufacturing/wearables_arena_set/` |

Detection plan: `boot_readiness/HARDWARE_PROFILE_DETECTION_PLAN.md`

---

## Workflow: hardware change → OS update

1. Hardware updates PRD, mechanical JSON, or OS contract
2. OS runs compatibility audit (`docs/HARDWARE_REPO_COMPATIBILITY_AUDIT.md`)
3. Update affected YAML profiles and policy modules
4. Refresh gap analysis and traceability matrix
5. Re-run simulated boot and CI checks
6. Do **not** bump release tier without new lab evidence

---

## Workflow: OS release with hardware claim

1. Hardware DVT/PVT/cert artifacts available
2. OS executes `hardware_release/HARDWARE_COMPATIBILITY_TEST_PLAN.md` P1+
3. Update evidence matrix to `validated`
4. Complete signoff template
5. Narrow claim boundary only to proven scope

---

## CI and validation scripts

| Repo | Script / workflow |
|------|-------------------|
| Hardware | `.github/workflows/hardware-package-ci.yml`, `scripts/validate_*` |
| OS | `.github/workflows/ci.yml`, hardware modules in pytest |

Cross-repo CI does not today gate on shared hardware evidence artifacts.

---

## Honest integration status

| Integration | Status |
|-------------|--------|
| Documentation cross-links | **complete** |
| Profile source path cites | **complete** |
| Bidirectional OS contract link | **complete** |
| Shared device ID auto-map | **planned** |
| DVT evidence ingestion | **not_started** |
| Production release coupling | **not_started** |

---

## Related documents

- [HARDWARE_OS_TRACEABILITY.md](HARDWARE_OS_TRACEABILITY.md)
- [HARDWARE_REPO_COMPATIBILITY_AUDIT.md](HARDWARE_REPO_COMPATIBILITY_AUDIT.md)
- [../hardware_compat/HARDWARE_REPO_SOURCE_MAP.md](../hardware_compat/HARDWARE_REPO_SOURCE_MAP.md)
