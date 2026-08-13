#!/bin/sh
# gunnchOS Device Lab Interactive Development Guest — first-boot hook.
#
# Placeholder only: this script is copied onto the rootfs by
# build_interactive_rootfs_alpine_aarch64.sh but is NOT wired into any init
# system yet (no openrc/service entry). It documents what a real first boot
# must do once the guest actually boots from the qcow2 root disk:
#
#   1. start seatd
#   2. start weston (Wayland compositor) on the virtio-gpu scanout
#   3. start pipewire (audio)
#   4. start gunnch-guest-agent listening on the virtio-serial chardev,
#      answering framebuffer_capture / compositor_info / app_launch for
#      real (not stubbed) — see guest_agent/PROTOCOL.md
#
# DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false.
# Not executed by any test; not claimed as a working init script.

echo "GUNNCHOS_INTERACTIVE_GUEST_FIRST_BOOT_PLACEHOLDER=true"
exit 0
