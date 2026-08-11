"""ECO-001 smoke — honest depth: topology + one aggregate session start."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.ecosystem.topology import ecosystem_topology
from gunnchos_device_os.device_lab.session import lab_artifact_root, start_session, stop_session


def run_eco001_smoke(*, repo_root: Path) -> dict[str, Any]:
    started = time.time()
    topo = ecosystem_topology()
    session = start_session("full_ecosystem", repo_root=repo_root)
    instance_id = session.get("instance_id")
    ok = bool(topo.get("ok") and session.get("ok") and instance_id)
    result = {
        "ok": ok,
        "scenario_id": "ECO-001",
        "depth": "smoke_topology_and_session",
        "topology": topo,
        "session": {
            "ok": session.get("ok"),
            "instance_id": instance_id,
            "profile_id": session.get("profile_id") or "full_ecosystem",
        },
        "simultaneous_multi_device": False,
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        "SILICON_EXACT_EMULATION": False,
        "duration_ms": int((time.time() - started) * 1000),
        "note": (
            "ECO-001 smoke only — not ECO-002..010, not chaos soak, not games lane. "
            "Master digital complete remains false."
        ),
    }
    evidence = lab_artifact_root(repo_root) / "ecosystem" / "ECO-001"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "result.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    if instance_id:
        stop_session(instance_id)
    return result
