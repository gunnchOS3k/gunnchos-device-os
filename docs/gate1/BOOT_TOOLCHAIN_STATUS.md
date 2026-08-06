# Boot Toolchain Status

## Offline software path — available

- Python 3 + `pytest` from `requirements.txt`
- No large dependency downloads required for Gate 1 boot/dock tests
- Commands:
  - `python -m gunnchos_device_os.boot --toolchain-check`
  - `PYTHONPATH=.:src pytest -q tests/test_gate1_*.py`

## Container smoke — optional

Repo already includes:

- `os_build/linux_desktop/docker-compose.yml`
- `os_build/image_prototype/Dockerfile`

If `docker` is installed, operators may run those paths manually. Default Gate 1 tests do **not** require Docker.

## QEMU full-system smoke — BLOCKED_TOOLCHAIN

**Status:** `BLOCKED_TOOLCHAIN`

The repository does not ship a QEMU full-system boot image or automated QEMU smoke harness for gunnchOS. Do not claim QEMU boot evidence until an image + script are added.

## Physical boot — pending

**Status:** `GUNNCHOS_PHYSICAL_BOOT_PENDING`

Use:

```bash
python -m gunnchos_device_os.boot --physical-capture
# or
python scripts/gunnchos_physical_boot_capture.py
```

Never treat the capture template as completed physical boot.
