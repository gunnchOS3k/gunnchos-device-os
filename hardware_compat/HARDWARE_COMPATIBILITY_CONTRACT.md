# Hardware Compatibility Contract

**Status:** contract documented · **not physically validated**

**Hardware repo:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Parties

| Party | Repository | Responsibility |
|-------|------------|----------------|
| Hardware industrial design | `gunnchos-hardware-industrial-design` | Mechanical, electrical, DVT/PVT, certification, production release |
| Device OS | `gunnchos-device-os` | Profile mirror, policy enforcement, boot readiness simulation, release evidence scaffolding |

---

## Contract surfaces

### 1. Product intent

| Hardware artifact | OS artifact |
|-------------------|-------------|
| `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` | `hardware_compat/device_profiles/*.yaml` |
| `product/PRODUCT_LINE_REQUIREMENTS.md` | `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md` |
| `architecture/DEVICE_COMPARISON_MATRIX.md` | `DEVICE_CLASS_COMPATIBILITY_MATRIX.md` |

### 2. OS/hardware interface

| Hardware artifact | OS artifact |
|-------------------|-------------|
| `docs/OS_HARDWARE_CONTRACT.md` | `docs/HARDWARE_SOFTWARE_CONTRACT.md` |
| `architecture/OS_HARDWARE_CONTRACT.md` | `docs/HARDWARE_REPO_INTEGRATION.md` |

### 3. Mechanical class

| Hardware artifact | OS artifact |
|-------------------|-------------|
| `mechanical_correctness/device_mechanical_targets.json` | `hardware_compat/device_profiles/*.yaml` → `hardware_repo_source_paths` |

### 4. Validation and release

| Hardware artifact | OS artifact |
|-------------------|-------------|
| `dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md` | `boot_readiness/DEVICE_BOOT_SEQUENCE.md` |
| `dvt/DVT_*_TEST_PLAN.md` | `hardware_release/HARDWARE_COMPATIBILITY_TEST_PLAN.md` |
| `certification/CERTIFICATION_EVIDENCE_REQUIRED.md` | `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` |
| `production_release/PRODUCTION_RELEASE_REQUIREMENTS.md` | `hardware_release/HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md` |

---

## OS obligations

1. Load device profiles that cite hardware source paths honestly.
2. Block or warn on unsupported mode/feature combinations per profile and engine rules.
3. Tag all compatibility results with evidence status (`real_hardware_validation_required` where applicable).
4. Never claim hardware-compatible release without linked lab evidence.
5. Preserve bidirectional traceability in `docs/HARDWARE_OS_TRACEABILITY.md`.

---

## Hardware obligations

1. Maintain canonical device class definitions in product and architecture docs.
2. Publish mechanical targets and maturity gate status without overstating EVT/DVT/PVT completion.
3. Provide DVT/PVT/certification evidence artifacts when available for OS evidence matrix linking.
4. Keep `docs/OS_HARDWARE_CONTRACT.md` aligned with OS-facing contract docs.

---

## Compatibility dimensions

Each device profile must document pass/warn/fail policy for:

- Display and external display / dock
- Input (keyboard, touch, stylus, controller)
- Audio, camera, mic
- Network and offline capability
- Storage and memory minimums
- Battery class and thermal class
- Supported modes, journey presets, and app packs
- Accessibility defaults
- Known gaps

Implementation: `gunnchos_device_os/hardware_compatibility_engine.py` and `hardware_*_policy.py` modules.

---

## Versioning and change control

| Change type | Update required |
|-------------|-----------------|
| New SKU | Hardware PRD + mechanical JSON + OS YAML profile + matrix row |
| Capability change | Hardware contract + OS profile + gap analysis |
| Validation evidence | Hardware DVT/PVT/cert docs + OS evidence matrix status |

---

## Claim boundary

This contract defines **documentation and profile alignment**. It is not evidence of physical compatibility. See [HARDWARE_CLAIM_BOUNDARY.md](HARDWARE_CLAIM_BOUNDARY.md).
