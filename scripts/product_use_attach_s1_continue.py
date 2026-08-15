#!/usr/bin/env python3
"""Attach to an already-running Interactive Guest and continue S1 closer legs.

Used when QEMU was left running (daemonized) after a host-side closer died —
NEVER starts a second QEMU. Prefer FAIL over false PASS. Tokens stay false.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient  # noqa: E402
from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    attempt_dsxl_dual_compositor_pass,
    attempt_ring_app_mutation_pass,
)
from gunnchos_device_os.device_lab.virtualization.qemu_guest import QemuGuestSession  # noqa: E402
from gunnchos_device_os.product_use.waike_guest_pack import write_guest_pack  # noqa: E402
from scripts.product_use_close_s1 import (  # noqa: E402
    OUT,
    run_g11,
    run_g13,
    run_g14,
    run_g15,
    update_persona_table,
)
from scripts.product_use_dock_reboot import dock_continuity, reboot_update_recovery  # noqa: E402


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def attach_session(work: Path) -> tuple[Any, dict[str, Any]]:
    pid_path = work / "qemu.pid"
    if not pid_path.exists():
        return None, {"ok": False, "error": "qemu_pid_missing"}
    pid = int(pid_path.read_text().strip())
    try:
        os.kill(pid, 0)
    except OSError:
        return None, {"ok": False, "error": "qemu_not_alive", "pid": pid}

    mon = work / "qemu-monitor.sock"
    ga = work / "guest-agent.sock"
    if not ga.exists():
        return None, {"ok": False, "error": "guest_agent_sock_missing"}

    sess = QemuGuestSession(work=work, profile={"profile_id": "dsxl_coder"}, repo_root=ROOT)
    sess.pid_file = pid_path
    sess.boot_log = work / "qemu_boot.log"
    sess.monitor_sock = mon.resolve() if mon.is_symlink() else mon
    sess.virtio_serial_sock = ga.resolve() if ga.is_symlink() else ga
    sess.agent = GuestAgentClient(
        sess.virtio_serial_sock,
        timeout_sec=10.0,
        extras={"transport_preference": "virtio_serial"},
    )
    sess.boot_complete = True
    sess.started_at = time.time()
    ping = sess.agent.call("ping", timeout_sec=8.0)
    if not ping.get("pong"):
        return None, {"ok": False, "error": "guest_agent_not_ready", "ping": ping}
    return sess, {"ok": True, "pid": pid, "ping": ping, "attached": True}


def main() -> int:
    started = _utc()
    work = ROOT / "artifacts/product_use/interactive_guest_session_s1"
    OUT.mkdir(parents=True, exist_ok=True)
    only_raw = (os.environ.get("PRODUCT_USE_S1_ONLY") or "").strip().upper()
    only = {x.strip() for x in only_raw.split(",") if x.strip()} if only_raw else set()

    pack_dir = ROOT / "artifacts/product_use/waike_guest_pack"
    pack = write_guest_pack(ROOT, pack_dir, course_id="GENERAL_IT")

    session, boot = attach_session(work)
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_002.s1_attach_continue.v1",
        "started_at_utc": started,
        "attach": boot,
        "pack": pack,
        "overlay_persona": os.environ.get("GUNNCH_LAB_OVERLAY_PERSONA"),
        "prefer_fail_over_false_pass": True,
        "tokens_remain_false": True,
        "only": sorted(only) if only else ["ALL"],
        "second_qemu": False,
    }
    if session is None or not boot.get("ok"):
        summary["error"] = boot.get("error") or "attach_failed"
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str))
        return 1

    def _want(name: str) -> bool:
        return (not only) or name in only

    results: dict[str, Any] = {}
    try:
        for _ in range(20):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2.0)

        if _want("RING"):
            ring_dir = OUT / "G11_ring"
            ring_dir.mkdir(parents=True, exist_ok=True)
            ring_ev = _evidence_dir(ROOT, "ring")
            results["RING"] = attempt_ring_app_mutation_pass(session, ring_ev)
            for name in ("RING_APP_MUTATION_EVIDENCE.json",):
                src = ring_ev / name
                if src.exists():
                    shutil.copy2(src, ring_dir / name)
            (ring_dir / "HONEST_REEARN_NOTE.json").write_text(
                json.dumps(
                    {
                        "attached_continue": True,
                        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
                            results["RING"].get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
                        ),
                        "RING_SPATIAL_ACCURACY": results["RING"].get("RING_SPATIAL_ACCURACY")
                        or "DIGITAL/SIMULATED",
                        "blocker": results["RING"].get("blocker"),
                    },
                    indent=2,
                )
                + "\n"
            )

        if _want("G11"):
            results["G11"] = run_g11(session)
            (OUT / "G11_waike").mkdir(parents=True, exist_ok=True)
            (OUT / "G11_waike" / "result.json").write_text(
                json.dumps(results["G11"], indent=2, default=str) + "\n"
            )

        if _want("G13"):
            results["G13"] = run_g13(session)
            (OUT / "G13_teacher").mkdir(parents=True, exist_ok=True)
            (OUT / "G13_teacher" / "result.json").write_text(
                json.dumps(results["G13"], indent=2, default=str) + "\n"
            )

        if _want("G14"):
            evidence_dir = OUT / "G14_dsxl_s1"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            results["G14"] = run_g14(session, evidence_dir)
            dsxl = attempt_dsxl_dual_compositor_pass(session, evidence_dir)
            results["G14"]["dsxl"] = dsxl
            (evidence_dir / "result.json").write_text(
                json.dumps(results["G14"], indent=2, default=str) + "\n"
            )

        if _want("G15"):
            results["G15"] = run_g15(session)
            (OUT / "G15_creative").mkdir(parents=True, exist_ok=True)
            (OUT / "G15_creative" / "result.json").write_text(
                json.dumps(results["G15"], indent=2, default=str) + "\n"
            )

        if _want("DOCK") or not only:
            results["DOCK"] = dock_continuity(session)
            (OUT / "DOCK_CONTINUITY.json").write_text(
                json.dumps(results["DOCK"], indent=2, default=str) + "\n"
            )

        if _want("REBOOT") or not only:
            results["REBOOT"] = reboot_update_recovery(session)
            (OUT / "REBOOT_UPDATE_RECOVERY.json").write_text(
                json.dumps(results["REBOOT"], indent=2, default=str) + "\n"
            )

        table = update_persona_table(results)
        summary["results"] = {k: {"ok": (v or {}).get("ok")} for k, v in results.items()}
        summary["persona_table"] = "artifacts/product_use/PERSONA_JOURNEY_TABLE.json"
        summary["finished_at_utc"] = _utc()
        summary["ok"] = True
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str))
        return 0
    except Exception as exc:  # noqa: BLE001
        summary["error"] = str(exc)
        summary["finished_at_utc"] = _utc()
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
