# Firmware Compatibility Layer

**Status:** harness exists · host/emulated tests pass · **physical-board validation pending**

The `firmware_compat/` directory provides OS-side firmware compatibility probing, manifest/contract comparison, and capsule-update simulation. It mirrors firmware artifacts from [gunnchos-hardware-industrial-design](../gunnchos-hardware-industrial-design) via [cross_repo_firmware_bridge/](../cross_repo_firmware_bridge/).

---

## What this layer does

- Runs host-side firmware probes (no root required)
- Compares probe output against OS profiles and imported firmware manifests/contracts
- Simulates capsule update staging (never flashes real firmware)
- Documents claim boundaries and implementation status

## What this layer does not do

- Prove physical gunnchOS hardware boot
- Run HLK or driver certification
- Flash or modify real firmware
- Claim production firmware compatibility on silicon

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).

---

## Directory layout

| Path | Purpose |
|------|---------|
| `probes/` | Host-side firmware probe modules |
| `compatibility/` | Compatibility engine, contract checker, capsule client |
| `fixtures/` | Sample probe outputs and capsule responses |
| `imported_hardware_contracts/` | Synced manifests/contracts from hardware repo |
| `host_probe_schema.json` | JSON schema for probe output |
| `IMPLEMENTATION_STATUS.md` | Component status |

---

## Quick start

```bash
# Sync contracts from hardware repo (falls back to imported copies if repo missing)
PYTHONPATH=. python3 cross_repo_firmware_bridge/sync_firmware_contracts.py

# Run probe for a device profile
PYTHONPATH=. python3 firmware_compat/probes/firmware_probe.py \
  --device student_14_5 \
  --output results/firmware_probe_student_14_5.json

# Evaluate compatibility
PYTHONPATH=. python3 scripts/run_firmware_compatibility_demo.py
```

---

## Related code

| Module | Role |
|--------|------|
| `compatibility/firmware_compatibility_engine.py` | Manifest + probe + contract evaluation |
| `cross_repo_firmware_bridge/sync_firmware_contracts.py` | Import hardware repo contracts |
| `hardware_compat/` | OS hardware profiles (YAML) |

---

## Claim boundary

Harness exists; host/emulated tests pass. Physical-board validation remains pending. No HLK, no physical boot claims.
