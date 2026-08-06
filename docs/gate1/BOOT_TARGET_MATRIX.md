# Gate 1 Boot Target Matrix

| Target class | Description | Software evidence | Physical evidence |
|---|---|---|---|
| `host-native` | Run probe on developer host with sample manifest | Supported via `python -m gunnchos_device_os.boot` | N/A (not a device boot) |
| `vm-container` | Optional Docker smoke using existing `os_build/` paths | Optional when Docker present | N/A |
| `physical-candidate` | Real device / board boot | Capture template only | **GUNNCHOS_PHYSICAL_BOOT_PENDING** |

## Status tokens

- `GUNNCHOS_BOOT_SOFTWARE_PATH_PASS` — offline software probe succeeded
- `GUNNCHOS_PHYSICAL_BOOT_PENDING` — physical boot not claimed

## Offline path (available deps only)

```bash
pip install -r requirements.txt   # pytest only
PYTHONPATH=.:src pytest -q tests/test_gate1_boot_probe.py
python -m gunnchos_device_os.boot --manifest config/boot/sample_manifest.json
```

## Toolchain honesty

See [BOOT_TOOLCHAIN_STATUS.md](BOOT_TOOLCHAIN_STATUS.md). QEMU full-system smoke is `BLOCKED_TOOLCHAIN`.
