# Firmware Host Probes

Host-side probes for firmware compatibility harness. Each module is runnable standalone and via `firmware_probe.py`.

**Rules:** no root required · graceful platform detection · no physical gunnchOS hardware claims unless `--fixture` provided.

| Module | Checks |
|--------|--------|
| `firmware_probe.py` | Orchestrates all probes |
| `uefi_probe.py` | UEFI/firmware env indicators |
| `acpi_probe.py` | ACPI tables / paths |
| `devicetree_probe.py` | DeviceTree paths |
| `display_probe.py` | Display enumeration hints |
| `dock_probe.py` | Dock / USB-C alt-mode hints |
| `battery_probe.py` | Battery status paths |
| `thermal_probe.py` | Thermal zone paths |
| `input_probe.py` | Input device hints |
| `storage_probe.py` | Storage enumeration |
| `network_probe.py` | Network interfaces |
