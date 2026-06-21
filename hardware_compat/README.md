# Hardware Compatibility Layer

**Status:** profile-based compatibility layer exists · **real hardware validation not proven**

The `hardware_compat/` directory holds device profiles and contract documents that mirror assumptions from the hardware industrial design repo ([`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)).

---

## What this layer does

- Loads per-SKU YAML profiles under `device_profiles/`
- Feeds `gunnchos_device_os/hardware_compatibility_engine.py` and policy modules
- Documents source mapping, claim boundaries, and validation status
- Provides an honest compatibility matrix for modes, inputs, and app packs

## What this layer does not do

- Prove physical hardware boot
- Replace HLK or driver certification
- Validate battery life, thermal behavior, or RF compliance on silicon
- Claim production hardware compatibility

See [HARDWARE_CLAIM_BOUNDARY.md](HARDWARE_CLAIM_BOUNDARY.md) for the authoritative claim text.

---

## Directory layout

| Path | Purpose |
|------|---------|
| `device_profiles/*.yaml` | Per-SKU capability and policy mirrors |
| `HARDWARE_COMPATIBILITY_CONTRACT.md` | Contract between OS layer and hardware repo |
| `HARDWARE_REPO_SOURCE_MAP.md` | Hardware artifact → OS artifact map |
| `HARDWARE_CLAIM_BOUNDARY.md` | Allowed and disallowed claims |
| `DEVICE_CLASS_COMPATIBILITY_MATRIX.md` | Mode/feature matrix by device class |
| `HARDWARE_VALIDATION_STATUS.md` | Validation evidence status |

---

## Device profiles

| Profile file | Device ID | Hardware repo key |
|--------------|-----------|-------------------|
| `student_14_5.yaml` | `student_14_5` | `student_14` in `device_mechanical_targets.json` |
| `handheld_hybrid.yaml` | `handheld_hybrid` | `handheld_hybrid` |
| `ds_xl_coder.yaml` | `ds_xl_coder` | `ds_xl_coder` |
| `wearables_arena_set.yaml` | `wearables_arena_set` | `wearables_arena_set` |

---

## Related code

| Module | Role |
|--------|------|
| `gunnchos_device_os/hardware_compatibility_engine.py` | Compatibility evaluation |
| `gunnchos_device_os/hardware_manifest_loader.py` | Profile loading |
| `gunnchos_device_os/hardware_*_policy.py` | Dimension-specific policy |
| `gunnchos_device_os/hardware_boot_readiness.py` | Simulated boot readiness |

---

## Validation

Compatibility rules: `config/hardware_compatibility_rules.yaml`  
Requirements baseline: `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md`

---

## Cross-repo links

- Hardware PRD: `../gunnchos-hardware-industrial-design/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md`
- Hardware OS contract: `../gunnchos-hardware-industrial-design/docs/OS_HARDWARE_CONTRACT.md`
- Mechanical targets: `../gunnchos-hardware-industrial-design/mechanical_correctness/device_mechanical_targets.json`
