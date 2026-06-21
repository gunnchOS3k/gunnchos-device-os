# Firmware Contract Sync Status

Last updated: 2026-06-21

| Field | Value |
|-------|-------|
| Sync script | `cross_repo_firmware_bridge/sync_firmware_contracts.py` |
| Import root | `firmware_compat/imported_hardware_contracts/` |
| Report | `results/firmware_contract_sync_report.json` |
| Hardware repo default | `../gunnchos-hardware-industrial-design` |
| CI fallback | committed imported copies when repo missing |

## Status

- Harness import path: **implemented**
- Cross-repo live sync: **available when hardware repo present**
- Physical-board contract validation: **pending**

Implemented in firmware compatibility harness / OS firmware probe / cross-repo contract sync. Physical-board validation remains pending.
