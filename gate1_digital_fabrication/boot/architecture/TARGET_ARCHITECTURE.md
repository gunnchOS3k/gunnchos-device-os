# G1-C1 Boot — Target Architecture (nonphysical)

Generated: 2026-08-07T22:25:26Z
Tokens: `GUNNCHOS_BOOT_SOFTWARE_PATH_PASS` · `GUNNCHOS_PHYSICAL_BOOT_PENDING`
Freeze: PHYSICAL_EXECUTION_FREEZE ACTIVE

## Architecture
- **Host-native probe**: Python `gunnchos_device_os.boot` against sample manifests (no device required).
- **Image prototype track**: `os_build/image_prototype/` containerized launcher + policy (development image).
- **Physical candidate**: single-board Linux class (Raspberry Pi 4 / CM4 or equivalent) — not claimed present.
- **Recovery**: A/B slot metadata + safe-mode contract under `firmware_compat/imported_hardware_contracts/boot/`.

## Non-goals (this package)
- Claiming a physical boot log
- Destructive flash of operator machines
