# Cross-Repo Firmware Bridge

Syncs firmware manifests and interface contracts from [gunnchos-hardware-industrial-design](../gunnchos-hardware-industrial-design) into `firmware_compat/imported_hardware_contracts/`.

---

## Usage

```bash
PYTHONPATH=. python3 cross_repo_firmware_bridge/sync_firmware_contracts.py
PYTHONPATH=. python3 cross_repo_firmware_bridge/sync_firmware_contracts.py \
  --hardware-repo ../gunnchos-hardware-industrial-design
```

If the hardware repo is missing, the sync script falls back to committed imported copies (CI-safe).

---

## Documents

| File | Purpose |
|------|---------|
| [HARDWARE_REPO_FIRMWARE_SOURCE_MAP.md](HARDWARE_REPO_FIRMWARE_SOURCE_MAP.md) | Source → import map |
| [FIRMWARE_ARTIFACT_IMPORT_PLAN.md](FIRMWARE_ARTIFACT_IMPORT_PLAN.md) | Import scope and cadence |
| [FIRMWARE_CONTRACT_SYNC_STATUS.md](FIRMWARE_CONTRACT_SYNC_STATUS.md) | Last sync status |

---

## Claim boundary

Implemented in firmware compatibility harness / OS firmware probe / cross-repo contract sync. Physical-board validation remains pending.
