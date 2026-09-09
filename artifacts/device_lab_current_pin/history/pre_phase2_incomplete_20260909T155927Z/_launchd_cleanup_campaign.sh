#!/bin/bash
set -x
LOG="/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation/artifacts/device_lab_current_pin/LAUNCHD_LOG.txt"
exec >>"$LOG" 2>&1
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) launchd start ==="
# quit monitors
for m in /tmp/gdli-*/mon.sock; do
  [ -S "$m" ] || continue
  printf 'quit\n' | nc -U "$m" || true
done
# kill qemu and campaign
/usr/bin/pkill -f 'qemu-system-aarch64' || true
/usr/bin/pkill -f 'run_current_pin_ring_only' || true
/usr/bin/pkill -f 'run_current_pin_17c_campaign' || true
sleep 3
/usr/bin/pkill -9 -f 'qemu-system-aarch64' || true
/usr/bin/pkill -9 -f 'run_current_pin_17c_campaign' || true
/usr/bin/pkill -9 -f 'run_current_pin_ring_only' || true
sleep 2
/bin/ps -ax -o pid,etime,command | /usr/bin/grep -E 'qemu-system|17c_campaign|ring_only' | /usr/bin/grep -v grep || echo 'clean'
export GUNNCH_GUEST_AGENT_HOST_STUB=0
export GUNNCHDEVICE_LAB_NET_RESTRICT=0
export GUNNCHDEVICE_LAB_INTERACTIVE_NET=1
export GUNNCH_LAB_INTERACTIVE_GUEST=1
export PYTHONPATH="/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation"
cd "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation"
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 scripts/run_current_pin_17c_campaign.py
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) campaign exit $? ==="
