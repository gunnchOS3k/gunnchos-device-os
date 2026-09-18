#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-artifacts/complete_experience/cx4_0/peripherals}"
mkdir -p "$OUT"
{
  echo "=== lsusb ==="; lsusb 2>&1 || true
  echo "=== bluetoothctl ==="; bluetoothctl devices 2>&1 || true
  echo "=== input devices ==="; libinput list-devices 2>&1 || true
  echo "=== lsblk ==="; lsblk -o NAME,TYPE,SIZE,MOUNTPOINT 2>&1 || true
} > "$OUT/peripheral_enum_$(date -u +%Y%m%dT%H%M%SZ).txt"
echo "physical_peripheral_pass=false" > "$OUT/STATUS.txt"
