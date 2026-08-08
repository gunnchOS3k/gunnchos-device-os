#!/usr/bin/env python3
"""Export runtime service matrix + supervisor smoke report."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.dual_screen_workflows import run_all_workflow_validations  # noqa: E402
from gunnchos_device_os.dock.continuity_sim_suite import run_continuity_simulation_suite  # noqa: E402
from gunnchos_device_os.runtime import RuntimeSupervisor, service_matrix  # noqa: E402


def main() -> int:
    out = ROOT / "results" / "full_product"
    out.mkdir(parents=True, exist_ok=True)
    matrix = service_matrix()
    (out / "service_matrix.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with tempfile.TemporaryDirectory() as tmp:
        sup = RuntimeSupervisor(persistence_root=tmp)
        started = sup.start_all()
        report = {
            "start": started,
            "status": sup.status_all(),
            "workflows": run_all_workflow_validations(),
            "dock_continuity": run_continuity_simulation_suite(),
        }
        sup.stop_all()
    (out / "runtime_supervisor_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(f"matrix_token={matrix.get('token')} services={matrix['count']}")
    print(f"started={len(started['started'])} faulted={started['faulted']}")
    print(f"workflow_token={report['workflows'].get('token')}")
    print(f"dock_tokens={report['dock_continuity'].get('status_tokens')}")
    return 0 if matrix["all_present"] and not started["faulted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
