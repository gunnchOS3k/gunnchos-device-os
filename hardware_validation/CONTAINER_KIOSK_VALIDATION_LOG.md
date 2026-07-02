# Container / Kiosk Validation Log

**Type:** Container kiosk prototype — **not** physical hardware validation.

## Evidence

- `os_build/linux_desktop/` — Docker nginx launcher (Phase 0)
- `os_build/image_prototype/` — kiosk packaging + healthcheck (Phase 2F)

## Validated (automated)

| Check | Command | Result |
|-------|---------|--------|
| Kiosk package build | `bash os_build/image_prototype/build_kiosk_package.sh` | pytest |
| Healthcheck | `bash os_build/image_prototype/healthcheck.sh` | pytest |
| No bootable OS claim | `artifact/MANIFEST.json` | `bootable_os_claim: false` |

## Not validated

- Physical handheld SKU
- VM image install
- Secure boot / TPM
