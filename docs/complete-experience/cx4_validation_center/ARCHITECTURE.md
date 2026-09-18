# Architecture

Local-first Validation Center:

1. Task library from CX4.0 packs (`library.py`)
2. Session store with autosave + immutable submission snapshots (`store.py`)
3. Accessible same-device UI (`apps/validation_center`)
4. Optional loopback static serve (`python -m gunnchos_device_os.cx4_validation_center serve-static`)
5. Reviewer signoff enforced before any later gate promotion (`gates.py`)
6. Collectors wired as SYSTEM_CAPTURED mocks only for UI contracts

No QEMU required for qualification.
