# Reproducible System Image Path (Digital)

**Status:** digital path implemented · `GUNNCHOS_REPRODUCIBLE_SYSTEM_IMAGE_DIGITAL_PASS` earned when validation suite passes  
**Not claimed:** bootable ISO/IMG, hardware boot, production signing, `FULL_OPERATIONAL_PRODUCT`

## What this track produces

A deterministic **DEV factory image bundle** under `artifacts/`:

| Artifact | Purpose |
|----------|---------|
| `blueprint.json` | Kernel/bootloader/init/drivers/fs/compositor/packages/sandbox/updater/recovery/VM target |
| `version_manifest.json` | Version/channel/SKU + claim flags |
| `sbom.cdx.json` | CycloneDX 1.5 SBOM |
| `provenance.json` | Reproducible build provenance |
| `dev_factory_image.json` | DEV factory stub (`DEV_SIGNED_NOT_PRODUCTION_FACTORY_IMAGE`) |
| `dev_signature.json` | DEV-realm HMAC stub (rejects production keys) |
| `CHECKSUMS.json` | Per-file SHA-256 |
| `sandbox_hook.json` / `updater_hook.json` / `recovery_hook.json` | Wired digital hooks |

Human notes live in `notes/`; compositor/unit stubs in `stubs/`.

## Build & validate

```bash
PYTHONPATH=.:src python3 -c "from gunnchos_device_os.system_image import build_and_validate; import json; print(json.dumps(build_and_validate(), indent=2))"
PYTHONPATH=.:src pytest -q tests/test_system_image.py
```

## Claim boundary

- Digital reproducible *path* only
- No production keys
- No physical boot evidence (`GUNNCHOS_PHYSICAL_SYSTEM_IMAGE_PENDING` always co-emitted)
- QEMU full-system smoke remains `BLOCKED_TOOLCHAIN` until CI harness lands
