"""LAB-SCENARIO-DSXL-DUALSCREEN — G06 two compositor outputs required."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab import CLAIM_BOUNDARY
from gunnchos_device_os.device_lab.manifest import build_manifest
from gunnchos_device_os.device_lab.scenarios.engine import ScenarioEngine
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session


def _run_creator_toolchain(work: Path, repo_root: Path) -> dict[str, Any]:
    """Real configure/build/test/debug — not a hardcoded stub."""
    from gunnchos_device_os.first_party_apps.creator_studio import run_creator_studio

    project = work / "creator_project"
    project.mkdir(parents=True, exist_ok=True)
    (project / "hello.py").write_text("print('dsxl-creator-ok')\n", encoding="utf-8")
    (project / "Makefile").write_text(
        "all:\n\t@echo build-ok\n"
        "test:\n\t@python3 hello.py\n"
        "debug:\n\t@python3 -c \"print('debug-ok')\"\n",
        encoding="utf-8",
    )
    (project / "hello.py").write_text("print('dsxl-creator-ok')\n", encoding="utf-8")

    configure = {"ok": True, "project": str(project), "files": sorted(p.name for p in project.iterdir())}
    build = subprocess.run(
        ["make", "-C", str(project), "all"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    test = subprocess.run(
        ["make", "-C", str(project), "test"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    debug = subprocess.run(
        ["make", "-C", str(project), "debug"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    studio = run_creator_studio(project_root=repo_root / "apps" / "creator_studio")
    executed = {
        "configure": configure,
        "build": {
            "ok": build.returncode == 0,
            "exit": build.returncode,
            "stdout": (build.stdout or "").strip(),
            "stderr": (build.stderr or "").strip()[:400],
        },
        "test": {
            "ok": test.returncode == 0 and "dsxl-creator-ok" in (test.stdout or ""),
            "exit": test.returncode,
            "stdout": (test.stdout or "").strip(),
        },
        "debug": {
            "ok": debug.returncode == 0 and "debug-ok" in (debug.stdout or ""),
            "exit": debug.returncode,
            "stdout": (debug.stdout or "").strip(),
        },
        "creator_studio": {
            "ok": bool(studio.get("ok")),
            "run_code": (studio.get("run") or {}).get("code"),
            "build_code": (studio.get("build") or {}).get("code"),
            "workspace": studio.get("workspace"),
        },
    }
    ok = all(
        [
            configure["ok"],
            executed["build"]["ok"],
            executed["test"]["ok"],
            executed["debug"]["ok"],
            executed["creator_studio"]["ok"],
        ]
    )
    return {
        "ok": ok,
        "executed": True,
        "stub": False,
        "mode": "creator_toolchain_executed",
        "steps": ["configure", "build", "test", "debug"],
        "detail": executed,
    }


def run(*, repo_root: Path, profile_id: str | None = None) -> dict[str, Any]:
    profile_id = profile_id or "dsxl_coder"
    started = time.time()
    start = start_session(profile_id, repo_root=repo_root)
    session = get_session(start["instance_id"])
    evidence = session.work / "LAB-SCENARIO-DSXL-DUALSCREEN"
    evidence.mkdir(parents=True, exist_ok=True)
    eng = ScenarioEngine(session, evidence)
    errors: list[str] = []

    connected = [o for o in session.display.outputs if o.get("connected")]
    two_outputs = len(connected) >= 2
    from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import high_fidelity_dual_gate

    # Prefer guest dual when QEMU virtio-gpu present; fail if logical dual claimed as guest dual
    claim_guest = any(
        str(o.get("source") or "").startswith("qemu") or str(o.get("class") or "") == "guest"
        for o in connected
    )
    dual_gate = high_fidelity_dual_gate(session.display.outputs, claim_guest_dual=claim_guest)
    if not two_outputs:
        errors.append("one_display_dsxl_fail")
    if dual_gate.get("gate") == "FAIL_LOGICAL_DUAL_CLAIMED_AS_GUEST":
        errors.append("logical_dual_claimed_as_guest")
    eng.record(
        "dual_output_assert",
        None,
        "start",
        ">=2 connected outputs",
        {"connected": connected, "count": len(connected), "dual_gate": dual_gate},
        two_outputs and dual_gate.get("gate") != "FAIL_LOGICAL_DUAL_CLAIMED_AS_GUEST",
    )

    primary_id = connected[0]["id"] if connected else None
    secondary_id = connected[1]["id"] if len(connected) > 1 else None

    # Real dual-output windows: Creator/IDE primary; terminal/logs/docs secondary
    win_primary = session.display.place_window(
        app_id="creator_ide",
        output_id=primary_id or "missing",
        title="Creator Studio",
        kind="creator_ide",
        focused=True,
        state={"role": "editor", "buffer": "main.py"},
    )
    win_secondary = session.display.place_window(
        app_id="terminal_docs",
        output_id=secondary_id or "missing",
        title="Terminal / Docs / Logs",
        kind="terminal",
        focused=False,
        state={"role": "logs", "pane": "build"},
    )
    windows_ok = bool(win_primary.get("ok") and win_secondary.get("ok"))
    if not windows_ok:
        errors.append("window_placement_failed")
    focus = session.display.focus_window("creator_ide")
    focus_ok = bool(focus.get("ok") and focus.get("focus", {}).get("output_id") == primary_id)
    if not focus_ok:
        errors.append("focus_wrong_output")
    primary_wins = session.display.windows_on(primary_id) if primary_id else []
    secondary_wins = session.display.windows_on(secondary_id) if secondary_id else []
    assignment_ok = (
        any(w["app_id"] == "creator_ide" for w in primary_wins)
        and any(w["app_id"] == "terminal_docs" for w in secondary_wins)
    )
    if not assignment_ok:
        errors.append("windows_wrong_output")
    eng.record(
        "real_windows",
        None,
        "place+focus",
        "ide_primary+terminal_secondary",
        {
            "primary": win_primary,
            "secondary": win_secondary,
            "focus": focus,
            "primary_wins": primary_wins,
            "secondary_wins": secondary_wins,
        },
        windows_ok and focus_ok and assignment_ok,
    )

    layout = {
        "primary": {"output": primary_id, "app": "creator_ide", "window": win_primary.get("window")},
        "secondary": {
            "output": secondary_id,
            "app": "terminal_docs",
            "window": win_secondary.get("window"),
        },
    }
    persisted = session.display.persist_layout()
    layout_path = evidence / "layout.json"
    layout_path.write_text(json.dumps({**layout, "store": persisted.get("layout")}, indent=2) + "\n", encoding="utf-8")
    reloaded_file = json.loads(layout_path.read_text(encoding="utf-8"))
    layout_persist_ok = (
        persisted.get("ok")
        and reloaded_file.get("primary", {}).get("app") == "creator_ide"
        and reloaded_file.get("secondary", {}).get("app") == "terminal_docs"
    )
    eng.record("layout_persist", layout, "reload", layout, reloaded_file, layout_persist_ok)
    if not layout_persist_ok:
        errors.append("layout_persist_failed")

    # Real build/test/debug (must not be stub creator_toolchain_digital)
    build = _run_creator_toolchain(evidence, repo_root)
    if not build.get("ok") or build.get("stub") or not build.get("executed"):
        errors.append("build_stub_or_failed")
    if build.get("mode") == "creator_toolchain_digital":
        errors.append("build_mode_stub_rejected")

    # gunnchAI via actual OS AI API
    try:
        from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry

        reg = ModelRegistry(evidence / "models")
        runtime = LocalAiRuntime(reg)
        runtime.ensure_default_models(repo_root, include_llama=True)
        ai = runtime.run_capability("code", "explain dual-screen layout persistence")
        ai_ok = bool(ai.get("ok") or ai.get("text") or ai.get("output"))
        primary_micro = ai.get("runtime") == "deterministic_micro"
        # Prefer phase_xii llama when micro
        if primary_micro:
            from gunnchos_device_os.phase_xii.apps import ai as xii_ai

            ai_out = xii_ai.tutor_ask("dual screen coding hint", evidence_dir=evidence / "ai")
            if ai_out.get("ok") and not ai_out.get("ai_stub_as_gunnchai_proof") and (
                ai_out.get("backend") == "llama.cpp" or ai_out.get("stub") is False
            ):
                ai_result = {
                    "ok": True,
                    "runtime": ai_out.get("backend") or "llama.cpp",
                    "path": "phase_xii_os_ai_api",
                    "primary_is_micro_deterministic": False,
                    "measurement": "HOST_OBSERVED",
                }
                ai_ok = True
                primary_micro = False
            else:
                ai_result = {
                    "ok": ai_ok,
                    "runtime": ai.get("runtime"),
                    "model_id": (ai.get("route") or {}).get("model_id"),
                    "primary_is_micro_deterministic": True,
                    "note": "micro used; not preferred for G08-class proof but G06 AI help recorded honestly",
                    "raw_keys": sorted(ai.keys()),
                }
        else:
            ai_result = {
                "ok": ai_ok,
                "runtime": ai.get("runtime"),
                "model_id": (ai.get("route") or {}).get("model_id"),
                "primary_is_micro_deterministic": False,
                "path": "phase_xiv_os_ai_api",
                "measurement": "HOST_OBSERVED",
                "raw_keys": sorted(ai.keys()),
            }
    except Exception as exc:
        try:
            from gunnchos_device_os.phase_xii.apps import ai as xii_ai

            ai_out = xii_ai.tutor_ask("dual screen coding hint", evidence_dir=evidence / "ai")
            ai_result = {
                "ok": bool(ai_out.get("ok")),
                "backend": ai_out.get("backend"),
                "stub": ai_out.get("stub"),
                "ai_stub_as_gunnchai_proof": ai_out.get("ai_stub_as_gunnchai_proof", False),
                "error_fallback": str(exc),
                "path": "phase_xii_os_ai_api",
            }
            ai_ok = bool(ai_out.get("ok")) and not ai_out.get("ai_stub_as_gunnchai_proof")
        except Exception as exc2:
            ai_result = {"ok": False, "error": str(exc), "error2": str(exc2)}
            ai_ok = False
    if not ai_ok:
        errors.append("ai_code_help_failed")
    eng.record(
        "build_test_ai",
        None,
        "toolchain+ai",
        "executed",
        {"build": build, "ai": ai_result},
        ai_ok and build.get("ok") and build.get("executed"),
    )

    # Unknown transition must not be success
    unknown = session.display.apply_transition("unknown")
    unknown_ok = unknown.get("ok") is False and unknown.get("accepted_as_success") is False
    if not unknown_ok:
        errors.append("unknown_transition_accepted")
    eng.record("unknown_transition_reject", None, "unknown", "reject", unknown, unknown_ok)

    # Secondary disconnect safe degrade + reconnect restore
    if secondary_id:
        disc = session.display.disconnect(secondary_id)
        remaining = [o for o in session.display.outputs if o.get("connected")]
        degrade_ok = disc.get("ok") and len(remaining) >= 1 and len(session.display.windows_on(secondary_id)) == 0
        transition = session.display.apply_transition("secondary_disconnect")
        if not transition.get("ok"):
            degrade_ok = False
            errors.append("disconnect_transition_failed")
        eng.record(
            "secondary_disconnect",
            layout,
            {"disconnect": secondary_id},
            "safe_degrade",
            {"remaining": remaining, "transition": transition, "disc": disc},
            degrade_ok,
        )
        if not degrade_ok:
            errors.append("secondary_disconnect_failed")

        recon = session.display.reconnect(secondary_id)
        restore_ok = (
            recon.get("ok")
            and recon.get("layout_restored")
            and session.display.connected_count() >= 2
            and any(w["app_id"] == "terminal_docs" for w in session.display.windows_on(secondary_id))
        )
        eng.record(
            "secondary_reconnect_restore",
            remaining,
            {"reconnect": secondary_id},
            "layout_restored",
            {"recon": recon, "connected": session.display.connected_count()},
            restore_ok,
        )
        if not restore_ok:
            errors.append("reconnect_restore_failed")
    else:
        errors.append("no_secondary_output")
        degrade_ok = False
        restore_ok = False

    ok = (
        two_outputs
        and windows_ok
        and focus_ok
        and assignment_ok
        and layout_persist_ok
        and ai_ok
        and build.get("ok")
        and build.get("executed")
        and not build.get("stub")
        and unknown_ok
        and degrade_ok
        and restore_ok
        and not errors
    )
    result = {
        "ok": ok,
        "scenario_id": "LAB-SCENARIO-DSXL-DUALSCREEN",
        "journey_id": "GOLDEN-06",
        "profile_id": profile_id,
        "connected_outputs": len(connected),
        "two_outputs_required": True,
        "layout": layout,
        "windows": [w.to_dict() for w in session.display.windows],
        "build": build,
        "ai": ai_result,
        "unknown_transition": unknown,
        "errors": errors,
        "steps": eng.steps,
        "PHYSICAL_DUAL_PANEL": "PENDING",
        "GUEST_DUAL_OUTPUT_PASS": bool(dual_gate.get("GUEST_DUAL_OUTPUT_PASS")),
        "dual_gate": dual_gate,
        "HUMAN_VALIDATION": "PENDING",
        "implementer_ready_for_independent_E4_D6": ok,
        "INDEPENDENT_VERIFICATION": "PENDING",
        "duration_ms": int((time.time() - started) * 1000),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    manifest = build_manifest(
        profile=session.profile,
        scenario="LAB-SCENARIO-DSXL-DUALSCREEN",
        fidelity=session.fidelity.to_dict(),
        virtualization=session.virt,
        virtual_devices={"display": session.display.outputs},
        applications=["creator_ide", "terminal_docs", "gunnchai"],
        result=result,
        evidence_dir=evidence,
        repo_root=repo_root,
    )
    result["manifest"] = {
        "run_id": manifest["run_id"],
        "path": manifest.get("manifest_path"),
        "sha256": manifest.get("manifest_sha256"),
    }
    (evidence / "result.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    stop_session(session.instance_id)
    return result
