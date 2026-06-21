# Firmware Artifact Import Plan

## Scope

Import read-only YAML/DSL descriptor stubs required by the OS firmware compatibility harness:

1. Per-SKU firmware manifests (4 devices)
2. Interface contracts (display, input, battery, thermal, storage, network, dock, power, edge_io)
3. Boot contracts (standard, recovery, safe mode)
4. Capsule update sample manifest
5. ACPI/DeviceTree descriptor stubs

## Cadence

- On hardware repo firmware changes: run `sync_firmware_contracts.py`
- CI: sync with fallback to committed `imported_hardware_contracts/` when sibling repo unavailable

## Out of scope

- Binary firmware images
- Flash programming tools
- HLK packages
- Production signing keys

## Validation

- `scripts/validate_firmware_compat.py`
- `scripts/validate_cross_repo_firmware_bridge.py`

Physical-board validation remains pending after import.
