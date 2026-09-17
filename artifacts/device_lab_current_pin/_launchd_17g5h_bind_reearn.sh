#!/bin/bash
set -euo pipefail
WT="/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation"
cd "$WT"
export GUNNCH_WAIKE_QEMU_FLOOR_GIB=15
export GUNNCH_GUEST_AGENT_HOST_STUB=0
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
LOG="$WT/artifacts/device_lab_current_pin/waike/WAIKE_RUN_LOG_17G5H_bind_reearn.txt"
echo "LAUNCHD_START $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
# Prove qemu works in launchd context
/opt/homebrew/bin/qemu-system-aarch64 -version >> "$LOG" 2>&1 || {
  echo "QEMU_VERSION_FAIL" >> "$LOG"
  exit 2
}
/usr/bin/python3 scripts/run_waike_gui_hub_journey_17g5h.py >> "$LOG" 2>&1
echo "LAUNCHD_EXIT:$?" >> "$LOG"
echo "LAUNCHD_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
