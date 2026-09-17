#!/bin/bash
set -euo pipefail
WT="/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation"
cd "$WT"
export GUNNCH_WAIKE_QEMU_FLOOR_GIB=15
export GUNNCH_GUEST_AGENT_HOST_STUB=0
export PYTHONPATH="$WT${PYTHONPATH:+:$PYTHONPATH}"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
LOG="$WT/artifacts/device_lab_current_pin/waike/WAIKE_RUN_LOG_17G5H_bind_reearn.txt"
MARKER="$WT/artifacts/device_lab_current_pin/waike/LAUNCHD_BIND_REEARN_STATUS.json"
echo "LAUNCHD_START $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
/opt/homebrew/bin/qemu-system-aarch64 -version >> "$LOG" 2>&1 || {
  echo "QEMU_VERSION_FAIL" >> "$LOG"
  printf '%s\n' '{"ok":false,"blocker":"qemu_version_fail"}' > "$MARKER"
  exit 2
}
echo "HVF_CHECK $(sysctl -n kern.hv_support 2>/dev/null || echo unknown)" >> "$LOG"
# Prove guestfwd cmd clause is active in this process tree
/usr/bin/python3 - <<'PY' >> "$LOG" 2>&1
import sys
sys.path.insert(0, ".")
from gunnchos_device_os.device_lab.guest_service_forward import device_lab_hub_only_forward
print("GUESTFWD_NETDEV", device_lab_hub_only_forward().qemu_netdev())
PY
/usr/bin/python3 scripts/run_waike_gui_hub_journey_17g5h.py >> "$LOG" 2>&1
EC=$?
echo "LAUNCHD_EXIT:$EC" >> "$LOG"
echo "LAUNCHD_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
/usr/bin/python3 - <<PY
import json
from pathlib import Path
from datetime import datetime, timezone
log = Path("$LOG")
text = log.read_text(errors="replace")
idx = text.rfind("{")
payload = {"ok": False, "exit": $EC, "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
if idx >= 0:
    try:
        # find last complete JSON by scanning backwards for prompt 17G.5H blocks
        for start in [i for i in range(len(text)) if text.startswith("{\n  \"generated_at_utc\"", i)][-1:]:
            pass
        import re
        matches = list(re.finditer(r"\{\n  \"generated_at_utc\".*?\n\}\n", text, re.S))
        if matches:
            payload.update(json.loads(matches[-1].group(0)))
    except Exception as e:
        payload["parse_error"] = repr(e)
payload["launchd_exit"] = $EC
Path("$MARKER").write_text(json.dumps(payload, indent=2) + "\n")
PY
exit "$EC"
