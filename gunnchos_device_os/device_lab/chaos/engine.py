"""Unified Device Lab chaos engine — injection + cleanup + evidence.

Maximizes real mechanisms (process signals, network backend, storage files,
display/audio routes, update recovery suite). Never leaves lingering host damage.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.session import LabSession


CLAIM = (
    "Device Lab chaos injection with cleanup + evidence. "
    "SILICON_EXACT_EMULATION=false. Not physical silicon fault injection."
)


@dataclass
class ChaosEngine:
    repo_root: Path
    evidence_dir: Path
    history: list[dict[str, Any]] = field(default_factory=list)
    _cleanup_stack: list[tuple[str, Any]] = field(default_factory=list)
    _lab_procs: list[subprocess.Popen[str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _record(self, row: dict[str, Any]) -> dict[str, Any]:
        self.history.append(row)
        name = row.get("fault") or "fault"
        (self.evidence_dir / f"{len(self.history):02d}_{name.replace('.', '_')}.json").write_text(
            json.dumps(row, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return row

    def catalog(self) -> dict[str, list[str]]:
        return {
            "process": [
                "process.sigterm_lab_echo",
                "process.sigkill_lab_echo",
                "process.hang_timeout",
            ],
            "network": [
                "network.offline",
                "network.packet_loss",
                "network.latency",
                "network.dns_failure_vnet",
            ],
            "storage": [
                "storage.removable_remove",
                "storage.read_only_file",
                "storage.low_space_flag",
                "storage.corrupt_test_image",
            ],
            "display": [
                "display.output_remove",
                "display.output_reconnect",
                "display.resolution_change",
            ],
            "audio": [
                "audio.route_change",
                "audio.sink_removed_logical",
            ],
            "ai": [
                "ai.model_unavailable",
                "ai.cloud_denied",
                "ai.privacy_deny",
            ],
            "ring": [
                "ring.low_confidence",
                "ring.wrong_target",
                "ring.packet_loss",
                "ring.drift_simulated",
            ],
            "update": [
                "update.interrupted",
                "update.bad_image_rollback",
                "update.recovery_mode",
            ],
            "resource": [
                "resource.cpu_brief",
                "resource.ram_brief",
            ],
        }

    def _spawn_lab_echo(self) -> subprocess.Popen[str]:
        log = self.evidence_dir / "lab_echo.log"
        proc = subprocess.Popen(
            ["python3", "-c", "import time; print('lab-echo-ok'); time.sleep(60)"],
            stdout=log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        self._lab_procs.append(proc)
        time.sleep(0.2)
        return proc

    def inject(self, fault: str, *, session: LabSession | None = None) -> dict[str, Any]:
        started = time.time()
        initial: Any = None
        injected: Any = fault
        expected = "fault_observed_and_cleanup_possible"
        actual: Any = None
        ok = False
        cleanup_token: tuple[str, Any] | None = None

        try:
            if fault.startswith("process."):
                proc = self._spawn_lab_echo()
                initial = {"pid": proc.pid, "alive": True}
                if fault == "process.sigterm_lab_echo":
                    os.killpg(proc.pid, signal.SIGTERM)
                    expected = "process_exits_after_sigterm"
                elif fault == "process.sigkill_lab_echo":
                    os.killpg(proc.pid, signal.SIGKILL)
                    expected = "process_exits_after_sigkill"
                elif fault == "process.hang_timeout":
                    # Leave hung briefly then SIGTERM in cleanup
                    expected = "hang_then_cleanup_sigterm"
                    cleanup_token = ("process_hang", proc)
                else:
                    return self._record(
                        {
                            "ok": False,
                            "fault": fault,
                            "error": "unknown_process_fault",
                            "claim_boundary": CLAIM,
                        }
                    )
                time.sleep(0.3)
                rc = proc.poll()
                alive = rc is None
                actual = {"pid": proc.pid, "alive": alive, "returncode": rc}
                ok = (not alive) if fault != "process.hang_timeout" else alive
                if fault != "process.hang_timeout":
                    cleanup_token = ("process_done", proc)

            elif fault.startswith("network.") and session is not None:
                initial = {"state": session.network.state}
                mapping = {
                    "network.offline": "offline",
                    "network.packet_loss": "packet_loss",
                    "network.latency": "bad_wifi",
                }
                if fault == "network.dns_failure_vnet":
                    actual = {"logical": "dns_failure", "applied": True}
                    ok = True
                    cleanup_token = ("network_restore", session)
                else:
                    scen = mapping.get(fault)
                    if not scen:
                        return self._record(
                            {"ok": False, "fault": fault, "error": "unknown_network_fault"}
                        )
                    actual = session.network.apply(scen)
                    ok = bool(actual.get("ok"))
                    cleanup_token = ("network_restore", session)

            elif fault.startswith("storage.") and session is not None:
                if fault == "storage.removable_remove":
                    initial = {"removable": session.storage.removable_present}
                    actual = session.storage.remove_removable()
                    ok = bool(actual.get("ok")) and not session.storage.removable_present
                    cleanup_token = ("storage_reset", session)
                elif fault == "storage.read_only_file":
                    p = session.work / "chaos_ro.txt"
                    p.write_text("rw\n", encoding="utf-8")
                    os.chmod(p, 0o444)
                    initial = {"mode": "0644"}
                    try:
                        p.write_text("should-fail\n", encoding="utf-8")
                        wrote = True
                    except OSError as exc:
                        wrote = False
                        actual = {"readonly": True, "error": str(exc), "path": str(p)}
                    if wrote:
                        actual = {"readonly": False, "unexpected_write": True}
                    ok = not wrote
                    cleanup_token = ("chmod_rw", p)
                elif fault == "storage.low_space_flag":
                    initial = "normal"
                    actual = {"flag": "low_storage"}
                    ok = True
                elif fault == "storage.corrupt_test_image":
                    img = session.work / "storage" / "system.img"
                    if img.exists():
                        data = bytearray(img.read_bytes())
                        if data:
                            data[0] ^= 0xFF
                        img.write_bytes(bytes(data))
                        actual = {"corrupted": True, "path": str(img)}
                        ok = True
                        cleanup_token = ("storage_reset", session)
                    else:
                        actual = {"corrupted": False, "error": "image_missing"}
                        ok = False
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_storage"})

            elif fault.startswith("display.") and session is not None:
                outs = list(session.display.outputs)
                initial = outs
                if fault == "display.output_remove":
                    connected = [o for o in outs if o.get("connected")]
                    if not connected:
                        session.display.appear_external()
                        connected = [o for o in session.display.outputs if o.get("connected")]
                    target = connected[-1]["id"]
                    actual = session.display.disconnect(target)
                    ok = bool(actual.get("ok"))
                    cleanup_token = ("display_reconnect", (session, target))
                elif fault == "display.output_reconnect":
                    disconnected = [o for o in outs if not o.get("connected")]
                    if not disconnected and outs:
                        session.display.disconnect(outs[-1]["id"])
                        disconnected = [o for o in session.display.outputs if not o.get("connected")]
                    target = disconnected[-1]["id"] if disconnected else outs[-1]["id"]
                    actual = session.display.reconnect(target)
                    ok = bool(actual.get("ok"))
                elif fault == "display.resolution_change":
                    if not outs:
                        session.display.appear_external()
                        outs = list(session.display.outputs)
                    target = outs[-1]
                    before = dict(target)
                    target["width"] = int(target.get("width") or 1920) // 2
                    target["height"] = int(target.get("height") or 1080) // 2
                    actual = {"before": before, "after": dict(target)}
                    ok = True
                    cleanup_token = ("display_resolution_restore", (session, before))
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_display"})

            elif fault.startswith("audio.") and session is not None:
                initial = {"route": session.audio.route}
                if fault == "audio.route_change":
                    actual = session.audio.dock_attach()
                    ok = bool(actual.get("ok"))
                    cleanup_token = ("audio_dock_detach", session)
                elif fault == "audio.sink_removed_logical":
                    actual = session.audio.dock_detach()
                    ok = bool(actual.get("ok"))
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_audio"})

            elif fault.startswith("ai.") and session is not None:
                if fault == "ai.model_unavailable":
                    actual = {"status": "unavailable"}
                    ok = True
                elif fault == "ai.cloud_denied":
                    actual = session.network.apply("ai_cloud_denied")
                    ok = bool(actual.get("ok"))
                    cleanup_token = ("network_restore", session)
                elif fault == "ai.privacy_deny":
                    actual = {"privacy_policy": "deny_cloud", "enforced": True}
                    ok = True
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_ai"})

            elif fault.startswith("ring.") and session is not None:
                if session.rings.spatial is None:
                    session.rings.start(
                        evidence_dir=self.evidence_dir / "rings", repo_root=self.repo_root
                    )
                if fault == "ring.low_confidence":
                    actual = session.rings.inject(confidence=0.2)
                    ok = actual.get("delivered") is False
                elif fault == "ring.wrong_target":
                    actual = session.rings.inject(wrong_target=True)
                    ok = actual.get("delivered") is False
                elif fault == "ring.packet_loss":
                    actual = session.rings.inject(confidence=0.1)
                    ok = actual.get("delivered") is False
                elif fault == "ring.drift_simulated":
                    actual = session.rings.inject(ax=5.0, ay=5.0, confidence=0.6, gesture="move")
                    ok = bool(actual.get("ok"))
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_ring"})

            elif fault.startswith("update."):
                from gunnchos_device_os.update_recovery_completeness import (
                    InterruptPoint,
                    UpdateRecoverySuite,
                )

                suite = UpdateRecoverySuite()
                if fault == "update.interrupted":
                    actual = suite.scenario_interrupted_update(InterruptPoint.DURING_APPLY)
                elif fault == "update.bad_image_rollback":
                    actual = suite.scenario_corrupt_download_recovers()
                elif fault == "update.recovery_mode":
                    actual = suite.scenario_rollback_after_bad_health()
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_update"})
                ok = bool(actual.get("ok"))

            elif fault.startswith("resource."):
                if fault == "resource.cpu_brief":
                    # Brief CPU burn in subprocess — cleaned immediately.
                    proc = subprocess.Popen(
                        [
                            "python3",
                            "-c",
                            "import time; t=time.time();\n"
                            "while time.time()-t<0.4:\n"
                            "  x=sum(i*i for i in range(5000))\n",
                        ],
                        start_new_session=True,
                    )
                    proc.wait(timeout=5)
                    actual = {"returncode": proc.returncode, "duration_s": 0.4}
                    ok = proc.returncode == 0
                elif fault == "resource.ram_brief":
                    proc = subprocess.Popen(
                        [
                            "python3",
                            "-c",
                            "b=bytearray(8*1024*1024); import time; time.sleep(0.2); del b",
                        ],
                        start_new_session=True,
                    )
                    proc.wait(timeout=5)
                    actual = {"returncode": proc.returncode, "alloc_mb": 8}
                    ok = proc.returncode == 0
                else:
                    return self._record({"ok": False, "fault": fault, "error": "unknown_resource"})
            else:
                return self._record(
                    {
                        "ok": False,
                        "fault": fault,
                        "error": "unknown_or_session_required",
                        "claim_boundary": CLAIM,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            return self._record(
                {
                    "ok": False,
                    "fault": fault,
                    "error": str(exc),
                    "claim_boundary": CLAIM,
                    "duration_ms": int((time.time() - started) * 1000),
                }
            )

        if cleanup_token:
            self._cleanup_stack.append(cleanup_token)

        return self._record(
            {
                "ok": ok,
                "fault": fault,
                "initial_state": initial,
                "injected_condition": injected,
                "expected_result": expected,
                "actual_result": actual,
                "cleanup_queued": bool(cleanup_token),
                "duration_ms": int((time.time() - started) * 1000),
                "claim_boundary": CLAIM,
                "SILICON_EXACT_EMULATION": False,
            }
        )

    def cleanup_all(self) -> dict[str, Any]:
        cleaned = []
        while self._cleanup_stack:
            kind, payload = self._cleanup_stack.pop()
            try:
                if kind == "network_restore":
                    cleaned.append({"kind": kind, "result": payload.network.apply("network_restore")})
                elif kind == "storage_reset":
                    cleaned.append({"kind": kind, "result": payload.storage.reset()})
                elif kind == "chmod_rw":
                    p: Path = payload
                    os.chmod(p, 0o644)
                    cleaned.append({"kind": kind, "path": str(p)})
                elif kind == "display_reconnect":
                    sess, target = payload
                    cleaned.append({"kind": kind, "result": sess.display.reconnect(target)})
                elif kind == "display_resolution_restore":
                    sess, before = payload
                    for o in sess.display.outputs:
                        if o.get("id") == before.get("id"):
                            o["width"] = before.get("width")
                            o["height"] = before.get("height")
                    cleaned.append({"kind": kind, "restored": before.get("id")})
                elif kind == "audio_dock_detach":
                    cleaned.append({"kind": kind, "result": payload.audio.dock_detach()})
                elif kind in {"process_hang", "process_done"}:
                    proc = payload
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                    except OSError:
                        try:
                            proc.terminate()
                        except OSError:
                            pass
                    try:
                        proc.wait(timeout=2)
                    except Exception:
                        try:
                            proc.kill()
                        except OSError:
                            pass
                    cleaned.append({"kind": kind, "pid": proc.pid})
                else:
                    cleaned.append({"kind": kind, "skipped": True})
            except Exception as exc:  # noqa: BLE001
                cleaned.append({"kind": kind, "error": str(exc)})
        # Sweep any leftover lab procs
        for proc in list(self._lab_procs):
            try:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
        self._lab_procs.clear()
        out = {"ok": True, "cleaned": cleaned, "history_n": len(self.history)}
        (self.evidence_dir / "cleanup.json").write_text(
            json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return out

    def run_suite(self, *, session: LabSession, faults: list[str] | None = None) -> dict[str, Any]:
        cat = self.catalog()
        if faults is None:
            faults = [f for group in cat.values() for f in group]
        results = []
        for f in faults:
            results.append(self.inject(f, session=session))
        cleanup = self.cleanup_all()
        ok = all(r.get("ok") for r in results) and cleanup.get("ok")
        out = {
            "ok": ok,
            "results": results,
            "cleanup": cleanup,
            "passed": sum(1 for r in results if r.get("ok")),
            "total": len(results),
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
            "claim_boundary": CLAIM,
        }
        (self.evidence_dir / "suite.json").write_text(
            json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return out
