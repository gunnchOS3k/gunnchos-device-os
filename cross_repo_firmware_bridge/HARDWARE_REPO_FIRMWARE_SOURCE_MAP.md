# Hardware Repo Firmware Source Map

Maps gunnchos-hardware-industrial-design firmware artifacts to OS-side imports.

| Hardware repo path | OS import path |
|--------------------|----------------|
| `firmware/manifests/*_firmware_manifest.yaml` | `firmware_compat/imported_hardware_contracts/manifests/` |
| `firmware/interfaces/*.yaml` | `firmware_compat/imported_hardware_contracts/interfaces/` |
| `firmware/boot/*.yaml` | `firmware_compat/imported_hardware_contracts/boot/` |
| `firmware/capsule_update/sample_capsule_manifest.yaml` | `firmware_compat/imported_hardware_contracts/capsule_update/` |
| `firmware/descriptors/acpi/*` | `firmware_compat/imported_hardware_contracts/descriptors/acpi/` |
| `firmware/descriptors/devicetree/*` | `firmware_compat/imported_hardware_contracts/descriptors/devicetree/` |

Sync script: `cross_repo_firmware_bridge/sync_firmware_contracts.py`

Default hardware repo path: `../gunnchos-hardware-industrial-design`
