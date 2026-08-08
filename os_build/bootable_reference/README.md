# Bootable Reference Image (DEV / QEMU)

**Status:** bootable under QEMU aarch64 when `GUNNCHOS_BOOTABLE_REFERENCE_IMAGE_DIGITAL_PASS` is earned  
**Not claimed:** physical device boot, production secure boot keys, `FULL_OPERATIONAL_PRODUCT`

## Layout

| Path | Purpose |
|------|---------|
| `overlay/` | gunnchOS init, services, shell, apps/games manifests, updater/recovery |
| `cache/` | Alpine minirootfs + virt kernel (gitignored; downloaded on build) |
| `work/` | Extracted rootfs staging (gitignored) |
| `artifacts/` | Packed initramfs, copied kernel, MANIFEST.json, BOOT_EVIDENCE.json |
| `../../results/full_product/bootable_reference/` | Serial boot log + evidence copies |

## Build & boot

Requires `qemu-system-aarch64` and `curl` (network on first cache fetch).

```bash
PYTHONPATH=.:src python3 scripts/build_bootable_reference_image.py
# or
make bootable-reference
```

## Claim boundary

Digital/VM boot evidence only. `GUNNCHOS_PHYSICAL_BOOT_PENDING` is always co-emitted.
