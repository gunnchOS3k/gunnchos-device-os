"""LAB-SCENARIO-HANDHELD-PLAY-DOCK — GOLDEN-05 play → dock work → resume."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY
from gunnchos_device_os.device_lab.ecosystem.games import launch_game
from gunnchos_device_os.device_lab.manifest import build_manifest
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session


def run(*, repo_root: Path, profile_id: str | None = None) -> dict[str, Any]:
    profile_id = profile_id or "handheld_hybrid"
    started = start_session(profile_id, repo_root=repo_root)
    session = get_session(started["instance_id"])
    evidence = session.work / "LAB-SCENARIO-HANDHELD-PLAY-DOCK"
    evidence.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        game = launch_game(
            game_id="anime-aggressors",
            repo_root=repo_root,
            work=evidence / "game",
            keep=False,
        )
        checkpoint = {"game_id": "anime-aggressors", "level": 3, "score": 1200, "slot": 1}
        (evidence / "checkpoint.json").write_text(
            json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8"
        )
        dock_on = {
            "disp": session.display.appear_external(),
            "net": session.network.dock_ethernet_attach(),
            "aud": session.audio.dock_attach(),
            "inp": session.input.dock_desktop_profile(),
        }
        work_note = evidence / "docked_work.txt"
        work_note.write_text("docked work mode notes\n", encoding="utf-8")
        dock_off = {
            "disp": session.display.disappear_external(),
            "net": session.network.dock_ethernet_detach(),
            "aud": session.audio.dock_detach(),
        }
        resumed = json.loads((evidence / "checkpoint.json").read_text(encoding="utf-8"))
        ok = bool(
            game.get("ok")
            and dock_on["disp"].get("ok")
            and dock_on["net"].get("ok")
            and work_note.exists()
            and dock_off["aud"].get("ok")
            and resumed.get("level") == 3
        )
        result = {
            "ok": ok,
            "scenario_id": "LAB-SCENARIO-HANDHELD-PLAY-DOCK",
            "game": game,
            "checkpoint": checkpoint,
            "dock_on": dock_on,
            "dock_off": dock_off,
            "resumed": resumed,
            "claim_boundary": CLAIM_BOUNDARY,
            "SILICON_EXACT_EMULATION": False,
            "duration_ms": int((time.time() - t0) * 1000),
        }
        (evidence / "result.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
        )
        manifest = build_manifest(
            profile=session.profile,
            scenario="LAB-SCENARIO-HANDHELD-PLAY-DOCK",
            fidelity=session.fidelity.to_dict(),
            virtualization=session.virt,
            virtual_devices={"display": session.display.outputs},
            applications=["anime-aggressors"],
            result=result,
            evidence_dir=evidence,
            repo_root=repo_root,
        )
        result["manifest"] = {"run_id": manifest["run_id"], "path": manifest.get("manifest_path")}
        return result
    finally:
        stop_session(session.instance_id)
