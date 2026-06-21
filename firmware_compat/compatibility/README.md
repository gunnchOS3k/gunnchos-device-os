# Firmware Compatibility Engine

Compares imported firmware manifests, OS device profiles, host probe output, and interface contracts.

| Module | Role |
|--------|------|
| `firmware_compatibility_engine.py` | Main evaluation |
| `descriptor_matcher.py` | Match ACPI/DeviceTree descriptor paths |
| `interface_contract_checker.py` | Validate required firmware interfaces |
| `capsule_update_client.py` | Simulated capsule staging |
| `boot_readiness_checker.py` | Harness boot readiness |

All modules return JSON-serializable dicts. Physical-board validation remains pending.
