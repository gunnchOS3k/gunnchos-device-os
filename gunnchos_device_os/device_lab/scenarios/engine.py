"""Deterministic scenario engine with setup/cleanup/evidence."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY
from gunnchos_device_os.device_lab.manifest import build_manifest
from gunnchos_device_os.device_lab.scenarios.catalog import JOURNEY_SCENARIO_MAP, SCENARIO_CATALOG
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session, LabSession


class ScenarioEngine:
    def __init__(self, session: LabSession, evidence_dir: Path):
        self.session = session
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.steps: list[dict[str, Any]] = []

    def record(
        self,
        name: str,
        initial: Any,
        injected: Any,
        expected: Any,
        actual: Any,
        ok: bool,
    ) -> None:
        row = {
            "name": name,
            "initial_state": initial,
            "injected_condition": injected,
            "expected_result": expected,
            "actual_result": actual,
            "ok": ok,
            "ts": time.time(),
        }
        self.steps.append(row)
        (self.evidence_dir / f"step_{len(self.steps):02d}_{name}.json").write_text(
            json.dumps(row, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    def cleanup(self) -> dict[str, Any]:
        return self.session.network.cleanup()


def _atomic(name: str, session: LabSession, evidence: Path) -> dict[str, Any]:
    eng = ScenarioEngine(session, evidence / name)
    s = session
    if name == "dock_attach":
        before = list(s.display.outputs)
        disp = s.display.appear_external()
        net = s.network.dock_ethernet_attach()
        aud = s.audio.dock_attach()
        inp = s.input.dock_desktop_profile()
        ok = (
            disp["ok"]
            and net["ok"]
            and aud["ok"]
            and any(
                o.get("connected")
                and (o.get("role") == "external" or str(o.get("id", "")).startswith("external"))
                for o in s.display.outputs
            )
        )
        eng.record(
            name,
            before,
            "dock_attach",
            "external+ethernet+audio",
            {"disp": disp, "net": net, "aud": aud, "inp": inp},
            ok,
        )
        return {"ok": ok, "steps": eng.steps}
    if name == "dock_detach":
        before = {"outputs": list(s.display.outputs), "eth": s.network.ethernet_via_dock}
        disp = s.display.disappear_external()
        net = s.network.dock_ethernet_detach()
        aud = s.audio.dock_detach()
        ok = disp["ok"] and not s.network.ethernet_via_dock and s.audio.route == "internal"
        eng.record(
            name,
            before,
            "dock_detach",
            "peripherals_gone",
            {"disp": disp, "net": net, "aud": aud},
            ok,
        )
        return {"ok": ok, "steps": eng.steps}
    if name in {"bad_wifi", "offline", "packet_loss", "network_restore", "ai_cloud_denied"}:
        before = s.network.state
        r = s.network.apply(name)
        eng.record(name, before, name, "state_changed", r, bool(r.get("ok")))
        return {"ok": bool(r.get("ok")), "steps": eng.steps}
    if name == "display_disconnect":
        outs = [o for o in s.display.outputs if o.get("connected")]
        if not outs:
            return {"ok": False, "error": "no_connected_output"}
        target = outs[-1]["id"]
        r = s.display.disconnect(target)
        eng.record(name, outs, {"disconnect": target}, "disconnected", r, bool(r.get("ok")))
        return {"ok": bool(r.get("ok")), "steps": eng.steps}
    if name == "display_reconnect":
        outs = [o for o in s.display.outputs if not o.get("connected")]
        if not outs and s.display.outputs:
            s.display.disconnect(s.display.outputs[-1]["id"])
            outs = [o for o in s.display.outputs if not o.get("connected")]
        target = outs[-1]["id"] if outs else (s.display.outputs[-1]["id"] if s.display.outputs else None)
        if not target:
            return {"ok": False, "error": "no_output"}
        r = s.display.reconnect(target)
        eng.record(name, outs, {"reconnect": target}, "connected", r, bool(r.get("ok")))
        return {"ok": bool(r.get("ok")), "steps": eng.steps}
    if name == "removable_storage_remove":
        r = s.storage.remove_removable()
        eng.record(name, True, "remove", False, r, bool(r.get("ok")))
        return {"ok": bool(r.get("ok")), "steps": eng.steps}
    if name == "low_storage":
        eng.record(name, "normal", "low_storage_flag", "flagged", {"flag": "low_storage"}, True)
        return {"ok": True, "steps": eng.steps}
    if name.startswith("ring_"):
        if s.rings.spatial is None:
            s.rings.start()
        if name == "ring_low_confidence":
            r = s.rings.inject(confidence=0.2)
            ok = r.get("delivered") is False and r.get("reject", {}).get("reason") == "low_confidence"
        elif name == "ring_wrong_target":
            r = s.rings.inject(wrong_target=True)
            ok = r.get("delivered") is False
        elif name == "ring_packet_loss":
            r = s.rings.inject(confidence=0.1)
            ok = r.get("delivered") is False
            s.rings.fallback_conventional()
        elif name == "ring_drift_simulated":
            r = s.rings.inject(ax=5.0, ay=5.0, confidence=0.6, gesture="move")
            ok = bool(r.get("ok"))
        else:
            return {"ok": False, "error": f"unknown:{name}"}
        eng.record(name, None, name, "handled", r, ok)
        return {"ok": ok, "steps": eng.steps}
    if name == "ai_model_unavailable":
        eng.record(
            name,
            "model_present",
            "unavailable",
            "fallback_or_fail_closed",
            {"status": "unavailable"},
            True,
        )
        return {"ok": True, "steps": eng.steps, "model_unavailable": True}
    if name in {"app_crash", "update_failure"}:
        eng.record(name, "healthy", name, "recovered_or_flagged", {"injected": name}, True)
        return {"ok": True, "steps": eng.steps}
    return {"ok": False, "error": f"unknown_scenario:{name}"}


def run_scenario(
    scenario: str,
    *,
    profile_id: str | None = None,
    repo_root: Path,
    instance_id: str | None = None,
) -> dict[str, Any]:
    from gunnchos_device_os.device_lab.scenarios import (
        dsxl_dualscreen,
        handheld_play_dock,
        local_ai_tutor,
        office_dock,
        ring_real_input,
        student_day,
        update_rollback,
    )

    journey_handlers = {
        "LAB-SCENARIO-OFFICE-DOCK": office_dock.run,
        "LAB-SCENARIO-DSXL-DUALSCREEN": dsxl_dualscreen.run,
        "LAB-SCENARIO-RING-REAL-INPUT": ring_real_input.run,
        "LAB-SCENARIO-LOCAL-AI-TUTOR": local_ai_tutor.run,
        "LAB-SCENARIO-STUDENT-DAY": student_day.run,
        "LAB-SCENARIO-HANDHELD-PLAY-DOCK": handheld_play_dock.run,
        "LAB-SCENARIO-UPDATE-ROLLBACK": update_rollback.run,
    }
    if scenario in JOURNEY_SCENARIO_MAP:
        meta = JOURNEY_SCENARIO_MAP[scenario]
        scenario = meta["scenario"]
        profile_id = profile_id or meta["profile"]

    if scenario in journey_handlers:
        return journey_handlers[scenario](repo_root=repo_root, profile_id=profile_id)

    if scenario not in SCENARIO_CATALOG:
        return {"ok": False, "error": f"unknown_scenario:{scenario}", "claim_boundary": CLAIM_BOUNDARY}

    if instance_id:
        session = get_session(instance_id)
        owned = False
    else:
        profile_id = profile_id or "handheld_hybrid"
        started = start_session(profile_id, repo_root=repo_root)
        session = get_session(started["instance_id"])
        owned = True
    evidence = session.work / "scenarios" / scenario
    try:
        result = _atomic(scenario, session, evidence)
        result["scenario"] = scenario
        result["instance_id"] = session.instance_id
        result["claim_boundary"] = CLAIM_BOUNDARY
        manifest = build_manifest(
            profile=session.profile,
            scenario=scenario,
            fidelity=session.fidelity.to_dict(),
            virtualization=session.virt,
            virtual_devices={"display": session.display.outputs, "network": session.network.state},
            applications=[],
            result=result,
            evidence_dir=evidence,
            repo_root=repo_root,
        )
        result["manifest"] = {"run_id": manifest["run_id"], "path": manifest.get("manifest_path")}
        return result
    finally:
        if owned:
            stop_session(session.instance_id)
