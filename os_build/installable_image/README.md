# GunnchOS Installable OS Image Track (Phase 4B)

**Status:** Prototype packaging track — **not** a bootable production OS image or signed ISO.

## Artifact types (honest labels)

| Type | Status | Path |
|------|--------|------|
| Container kiosk prototype | Built (Phase 2F) | `os_build/image_prototype/` |
| Installable OS image bundle (prototype) | **This track** | `os_build/installable_image/` |
| Bootable ISO/IMG (x86_64) | Not built | Documented path only |
| Hardware boot on target SKU | Not validated | `hardware_validation/BOOT_VALIDATION_TEMPLATE.md` |

## What this track produces

A versioned **installable image prototype bundle** (`.tar.gz`) containing:

- Built launcher static files
- Policy + config snapshot
- Prototype install/uninstall stubs (documented, not production installer)
- `MANIFEST.json` with explicit claim boundaries
- SHA-256 checksum sidecar

This is an **internal OS-layer packaging prototype**. It does **not** include a bootloader, kernel, initramfs, or raw disk image.

## Build

```bash
bash scripts/build_installable_image.sh
python3 scripts/validate_installable_image_artifacts.py
```

## Validation

```bash
bash os_build/installable_image/healthcheck.sh
pytest tests/test_installable_image.py -q
```

## Path to real installable image

1. Complete Yocto/meta-gunnchos layer (see `os_build/yocto/`)
2. Produce signed ISO/IMG per `requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md`
3. Fill `hardware_validation/BOOT_VALIDATION_TEMPLATE.md` with boot evidence
4. Only then may `bootable_os_claim` advance beyond `false`
