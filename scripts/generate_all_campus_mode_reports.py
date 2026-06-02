#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gunnchos_launcher.campus_modes import list_campuses, load_mode

out = Path("results/campus_device_modes")
out.mkdir(parents=True, exist_ok=True)
for s in list_campuses():
    m = load_mode(s)
    (out / f"{s}_mode_report.md").write_text(f"# Mode — {s}\n\nDefault: {m['default_mode']}\n", encoding="utf-8")
    (out / f"{s}_device_state.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    (out / f"{s}_privacy_policy.md").write_text(f"# Privacy — {s}\n\nTelemetry: {m['telemetry_policy']}\n", encoding="utf-8")
print("Wrote campus device mode reports")
