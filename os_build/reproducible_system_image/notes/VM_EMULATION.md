# VM / emulation target

{
  "primary": "qemu-system-x86_64",
  "machine": "q35",
  "firmware": "OVMF (UEFI)",
  "status": "documented_target",
  "full_system_smoke": "BLOCKED_TOOLCHAIN until QEMU harness wired in CI",
  "alternate": "Docker os_build/image_prototype kiosk (userspace only)"
}
