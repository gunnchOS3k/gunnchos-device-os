# meta-gunnchos Yocto Layer (stub → Phase 1+)

Target: ARM64 handheld images for GunnchOS devices.

## Planned structure

```
meta-gunnchos/
├── conf/layer.conf
├── recipes-core/gunnchos-shell/gunnchos-shell.bb
├── recipes-core/images/gunnchos-image.bb
└── recipes-kernel/linux/linux-gunnchos_%.bbappend
```

## Phase 0 status

Not started. Use `os_build/linux_desktop/` Docker prototype for Phase 0 shell validation.

## Hardware targets

- ARM64 (primary): Qualcomm/Rockchip-class handheld SoCs
- x86_64 (dev/CI): container and lab images

## Image contents (planned)

- Linux kernel + systemd
- Wayland compositor (wlroots-based)
- GunnchOS shell (Electron or native Wayland kiosk)
- Container runtime for Linux apps (Level 3)
- Android compatibility layer stub (Level 4)

See `docs/USER_FOCUSED_OS_ARCHITECTURE.md` for the experience layer design.
