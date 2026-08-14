#!/usr/bin/env python3
"""PRODUCT-USE-RC-002 — handheld/dock continuity + reboot/update/recovery probes.

Runs INSIDE an already-booted Interactive Guest session when possible; otherwise
boots one. Prefer FAIL over false PASS. Tokens remain false unless earned.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    boot_interactive_guest,
)
from gunnchos_device_os.product_use.host_storage import preflight  # noqa: E402

OUT = ROOT / "artifacts" / "product_use" / "journeys"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dock_continuity(session: Any) -> dict[str, Any]:
    """Probe dual-output / dock-like continuity and failure cases."""
    before = _agent_call(session, "compositor_info", timeout_sec=15.0)
    outs = before.get("outputs") or before.get("guest_outputs") or []
    # Failure case: remove secondary (simulated via weston/output query honesty)
    fail = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; "
            "echo OUTPUTS_BEFORE=$(weston-info 2>/dev/null | grep -c wl_output || echo 0); "
            "test -d /var/lib/gunnchos && echo STATE_DIR_OK || echo STATE_DIR_MISSING; "
            "ls /sys/class/drm 2>/dev/null | head; "
            "echo DOCK_MARKER=$(test -f /var/lib/gunnchos/dock_state.json && echo PRESENT || echo ABSENT)",
        ],
        timeout_sec=30.0,
    )
    # Write a dock continuity marker then "detach" by renaming (failure case)
    write = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "mkdir -p /var/lib/gunnchos; "
            "printf '{\"docked\":true,\"ts\":%s}\\n' \"$(date +%s)\" > /var/lib/gunnchos/dock_state.json; "
            "cp /var/lib/gunnchos/dock_state.json /var/lib/gunnchos/dock_state.json.bak; "
            "mv /var/lib/gunnchos/dock_state.json /var/lib/gunnchos/dock_state.json.detached; "
            "echo DETACHED=$(test ! -f /var/lib/gunnchos/dock_state.json && echo OK || echo FAIL); "
            "mv /var/lib/gunnchos/dock_state.json.detached /var/lib/gunnchos/dock_state.json; "
            "echo REATTACHED=$(test -f /var/lib/gunnchos/dock_state.json && echo OK || echo FAIL); "
            "cat /var/lib/gunnchos/dock_state.json",
        ],
        timeout_sec=20.0,
    )
    stdout = (write.get("stdout") or "") + "\n" + (fail.get("stdout") or "")
    ok = "DETACHED=OK" in stdout and "REATTACHED=OK" in stdout
    return {
        "ok": ok,
        "observation_class": "GUEST_OBSERVED" if ok else "OPEN",
        "compositor_outputs": outs,
        "stdout": stdout[-1200:],
        "failure_cases_exercised": ["dock_state_detach_reattach"],
        "note": (
            "Guest FS dock-state continuity probe. Not physical dock silicon. "
            "HANDHELD_DOCK_CONTINUITY token not earned from FS marker alone."
        ),
        "HANDHELD_DOCK_CONTINUITY_PASS": False,
    }


def reboot_update_recovery(session: Any) -> dict[str, Any]:
    """Persona state survive reboot / simulated update interrupt / recovery marker."""
    seed = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "mkdir -p /var/lib/gunnchos/persona; "
            "printf '{\"persona\":\"G11\",\"lesson\":\"GENERAL_IT-w01\",\"progress\":1}\\n' "
            "> /var/lib/gunnchos/persona/state.json; "
            "echo SEED_OK; cat /var/lib/gunnchos/persona/state.json",
        ],
        timeout_sec=15.0,
    )
    # Simulated update interrupt: write staging then abort
    upd = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "mkdir -p /var/lib/gunnchos/update; "
            "echo staging > /var/lib/gunnchos/update/staging.flag; "
            "rm -f /var/lib/gunnchos/update/staging.flag; "
            "echo INTERRUPTED_CLEAN; "
            "echo RECOVERY=$(test -s /var/lib/gunnchos/persona/state.json && echo STATE_INTACT || echo STATE_LOST)",
        ],
        timeout_sec=15.0,
    )
    # Soft reboot via guest agent if supported; else mark NOT_RUN for hard reboot
    reboot = _agent_call(session, "reboot", timeout_sec=10.0) if False else {
        "ok": False,
        "skipped": True,
        "reason": "hard_reboot_deferred_use_persist_disk_reopen",
    }
    # Re-read state without hard reboot (persist disk continuity proxy)
    reread = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "echo REREAD=$(test -s /var/lib/gunnchos/persona/state.json && echo OK || echo FAIL); "
            "cat /var/lib/gunnchos/persona/state.json 2>/dev/null | head -c 200",
        ],
        timeout_sec=10.0,
    )
    out = (upd.get("stdout") or "") + "\n" + (reread.get("stdout") or "")
    ok = "RECOVERY=STATE_INTACT" in out and "REREAD=OK" in out and "SEED_OK" in (seed.get("stdout") or "")
    return {
        "ok": ok,
        "observation_class": "GUEST_OBSERVED_PARTIAL" if ok else "OPEN",
        "seed": {k: seed.get(k) for k in ("ok", "stdout")},
        "update_interrupt": {k: upd.get(k) for k in ("ok", "stdout")},
        "hard_reboot": reboot,
        "reread": {k: reread.get(k) for k in ("ok", "stdout")},
        "note": (
            "In-session persist + update-interrupt recovery. Hard guest reboot/reopen "
            "not claimed PASS in this probe."
        ),
        "REBOOT_UPDATE_RECOVERY_PASS": False,
    }


def main() -> int:
    space = preflight(ROOT, cleanup_if_tight=False)
    if space.get("HOST_RESOURCE_BLOCKED"):
        print(json.dumps({"HOST_RESOURCE_BLOCKED": True, "host_storage": space}, indent=2))
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    work = ROOT / "artifacts/product_use/interactive_guest_session_dock"
    work.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    boot = boot_interactive_guest(
        ROOT,
        work,
        dual=True,
        boot_timeout_s=int(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "300")),
        memory_mb=2048,
    )
    session = boot.pop("_session", None)
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_002.dock_reboot.v1",
        "started_at_utc": _utc(),
        "boot_ok": bool(boot.get("ok")),
        "host_storage": space.get("after"),
    }
    if not boot.get("ok") or session is None:
        summary["error"] = boot.get("error") or "boot_failed"
        (OUT / "DOCK_REBOOT_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 1
    try:
        for _ in range(15):
            if _agent_call(session, "compositor_info", timeout_sec=8.0).get("available"):
                break
            time.sleep(2.0)
        summary["dock"] = dock_continuity(session)
        summary["reboot_update_recovery"] = reboot_update_recovery(session)
        summary["HANDHELD_DOCK_CONTINUITY_PASS"] = False
        summary["REBOOT_UPDATE_RECOVERY_PASS"] = False
        summary["finished_at_utc"] = _utc()
    finally:
        try:
            session.stop()
        except Exception:  # noqa: BLE001
            pass
    (OUT / "DOCK_REBOOT_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
