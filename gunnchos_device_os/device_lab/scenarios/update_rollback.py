"""LAB-SCENARIO-UPDATE-ROLLBACK — GOLDEN-09 failed update rollback (existing suite)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY
from gunnchos_device_os.device_lab.manifest import build_manifest
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session
from gunnchos_device_os.update_recovery_completeness import (
    InterruptPoint,
    UpdateRecoverySuite,
)


def run(*, repo_root: Path, profile_id: str | None = None) -> dict[str, Any]:
    profile_id = profile_id or "student_14_5"
    started = start_session(profile_id, repo_root=repo_root)
    session = get_session(started["instance_id"])
    evidence = session.work / "LAB-SCENARIO-UPDATE-ROLLBACK"
    evidence.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        # Preserve a user-data marker to prove intact after rollback.
        user_data = session.work / "user_data.json"
        user_data.write_text(
            json.dumps({"docs": ["notes.md"], "keep": True}, indent=2) + "\n",
            encoding="utf-8",
        )
        suite = UpdateRecoverySuite()
        suite.user_state = {
            "profile": "student",
            "apps": ["launcher", "notes"],
            "marker": "GOLDEN-09",
        }
        corrupt = suite.scenario_corrupt_download_recovers()
        interrupted = suite.scenario_interrupted_update(InterruptPoint.DURING_APPLY)
        rollback = suite.scenario_rollback_after_bad_health()
        intact = user_data.exists() and '"keep": true' in user_data.read_text(encoding="utf-8")
        ok = bool(
            corrupt.get("ok") and interrupted.get("ok") and rollback.get("ok") and intact
        )
        result = {
            "ok": ok,
            "scenario_id": "LAB-SCENARIO-UPDATE-ROLLBACK",
            "corrupt": corrupt,
            "interrupted": interrupted,
            "rollback": rollback,
            "user_data_intact": intact,
            "claim_boundary": CLAIM_BOUNDARY,
            "SILICON_EXACT_EMULATION": False,
            "duration_ms": int((time.time() - t0) * 1000),
            "note": "Wires existing UpdateRecoverySuite into Device Lab Golden path.",
        }
        (evidence / "result.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
        )
        manifest = build_manifest(
            profile=session.profile,
            scenario="LAB-SCENARIO-UPDATE-ROLLBACK",
            fidelity=session.fidelity.to_dict(),
            virtualization=session.virt,
            virtual_devices={},
            applications=[],
            result=result,
            evidence_dir=evidence,
            repo_root=repo_root,
        )
        result["manifest"] = {"run_id": manifest["run_id"], "path": manifest.get("manifest_path")}
        return result
    finally:
        stop_session(session.instance_id)
