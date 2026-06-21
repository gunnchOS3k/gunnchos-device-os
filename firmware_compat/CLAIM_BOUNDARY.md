# Firmware Compatibility Claim Boundary

**Status:** enforced in probes and engine · **do not overclaim**

---

## Authoritative boundary text

This firmware compatibility harness probes the host OS environment and compares results against imported firmware manifests and interface contracts. It does not prove physical gunnchOS hardware boot, HLK certification, real firmware flashing, or production firmware compatibility on reference boards.

---

## Allowed claims today

| Claim | Basis |
|-------|-------|
| Host-side firmware probe ran for device profile X | `firmware_probe.py` output JSON |
| Firmware manifest loaded from hardware repo sync | `imported_hardware_contracts/` |
| Interface contract check passed in harness | `interface_contract_checker.py` |
| Capsule update simulated (not flashed) | `capsule_update_client.py` with `simulated_only: true` |
| Boot readiness check passed in harness | `boot_readiness_checker.py` with simulated status |

---

## Disallowed claims today

| Claim | Why not |
|-------|---------|
| gunnchOS boots on reference hardware for SKU X | No physical boot logs linked |
| Firmware compatible release | All validation harness/host-based |
| HLK or UEFI certification complete | Not run |
| Capsule update validated on silicon | Simulation only |
| ACPI/DeviceTree matches production board | Descriptor stubs only |
| Physical dock/display hotplug proven | Host probe or fixture only |

---

## Probe rules

- Probes detect host OS and platform indicators gracefully
- Probes never require root privileges
- Probes never claim physical gunnchOS hardware unless an explicit `--profile` or `--fixture` is provided
- Default runs are labeled `host_environment: true`

---

## Evidence tags

The compatibility engine attaches `physical_board_validation_pending` to evaluation results. Treat this tag as a **blocker for external firmware-compatible release messaging**.

---

## Related documents

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- [../cross_repo_firmware_bridge/FIRMWARE_CONTRACT_SYNC_STATUS.md](../cross_repo_firmware_bridge/FIRMWARE_CONTRACT_SYNC_STATUS.md)
- [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md)
