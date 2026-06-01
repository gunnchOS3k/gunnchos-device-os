#!/usr/bin/env python3
"""Generate device OS E2E report artifacts."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_launcher.research_measurement_mode import run_measurement_session
from gunnchos_launcher.seven_gc_bridge import export_seven_gc_device_state
from gunnchos_launcher.deploy_contract import simulate_deploy

def main():
    e2e = ROOT / "results" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    session = run_measurement_session("student_14_5")
    state = export_seven_gc_device_state("student_14_5", "school")
    deploy = simulate_deploy()
    report = {
        "measurement_session": session,
        "seven_gc_state": state,
        "deploy_simulation": deploy,
    }
    (e2e / "device_os_e2e_report.json").write_text(json.dumps(report, indent=2) + "\n")
    (e2e / "device_os_e2e_report.md").write_text(
        "# Device OS E2E Report\n\n"
        + "\n".join(f"- **{k}**: present" for k in report)
        + "\n\nSynthetic mock only.\n"
    )
    (e2e / "seven_gc_device_export.json").write_text(json.dumps(state, indent=2) + "\n")
    print(f"Wrote {e2e}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
