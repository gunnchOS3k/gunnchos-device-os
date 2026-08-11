"""LAB-SCENARIO-STUDENT-DAY — GOLDEN-01 student assignment then recreation."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY
from gunnchos_device_os.device_lab.ecosystem.continuity import seed_student_project
from gunnchos_device_os.device_lab.ecosystem.games import launch_game
from gunnchos_device_os.device_lab.manifest import build_manifest
from gunnchos_device_os.device_lab.session import start_session, stop_session


def run(*, repo_root: Path, profile_id: str | None = None) -> dict[str, Any]:
    profile_id = profile_id or "student_14_5"
    started = start_session(profile_id, repo_root=repo_root)
    from gunnchos_device_os.device_lab.session import get_session

    session = get_session(started["instance_id"])
    evidence = session.work / "LAB-SCENARIO-STUDENT-DAY"
    evidence.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        assignment = seed_student_project(session.work, title="GOLDEN-01 assignment")
        # Mark submitted
        receipt = {
            "submitted": True,
            "assignment_sha": assignment.get("content_sha256"),
            "at": time.time(),
        }
        (evidence / "submit_receipt.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        game = launch_game(
            game_id="anime-aggressors",
            repo_root=repo_root,
            work=evidence / "game",
            keep=False,
        )
        # Return to intact work
        project = session.work / "continuity/project.json"
        intact = project.exists() and "GOLDEN-01 assignment" in project.read_text(encoding="utf-8")
        ok = bool(assignment.get("ok") and receipt["submitted"] and game.get("ok") and intact)
        result = {
            "ok": ok,
            "scenario_id": "LAB-SCENARIO-STUDENT-DAY",
            "assignment": assignment,
            "receipt": receipt,
            "game": game,
            "work_intact": intact,
            "claim_boundary": CLAIM_BOUNDARY,
            "SILICON_EXACT_EMULATION": False,
            "duration_ms": int((time.time() - t0) * 1000),
        }
        (evidence / "result.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
        )
        manifest = build_manifest(
            profile=session.profile,
            scenario="LAB-SCENARIO-STUDENT-DAY",
            fidelity=session.fidelity.to_dict(),
            virtualization=session.virt,
            virtual_devices={"network": session.network.state},
            applications=["anime-aggressors"],
            result=result,
            evidence_dir=evidence,
            repo_root=repo_root,
        )
        result["manifest"] = {"run_id": manifest["run_id"], "path": manifest.get("manifest_path")}
        return result
    finally:
        stop_session(session.instance_id)
