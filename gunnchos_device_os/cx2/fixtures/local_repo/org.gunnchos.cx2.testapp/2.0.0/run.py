#!/usr/bin/env python3
"""CX2 authentic test app v2.0.0 — real process evidence."""
import json, os, sys, time
from pathlib import Path
marker = Path(os.environ.get("CX2_APP_RUNTIME", ".")) / "RUNNING.json"
marker.write_text(json.dumps({
  "app_id": "org.gunnchos.cx2.testapp",
  "version": "2.0.0",
  "pid": os.getpid(),
  "argv": sys.argv,
  "started_at": time.time(),
}) + "\n")
# Stay alive briefly so launch harness can observe pid
time.sleep(float(os.environ.get("CX2_APP_HOLD_SECS", "0.4")))
print(f"cx2-testapp-2.0.0-ok pid={os.getpid()}")
