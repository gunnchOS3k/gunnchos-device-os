#!/usr/bin/env python3
"""Current-pin RING-only re-earn with fail-closed wall clock.

Do not compete for the guest-agent socket from other processes while this runs.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "artifacts/device_lab_current_pin/RING_REEARN.json"
LOG_PREFIX = "RING_ONLY"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    started = time.time()
    out: dict = {
        "schema": "gunnchos.device_lab.current_pin.ring_reearn.v1",
        "started_at_utc": _utc(),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
    }
    session = None
    try:
        from scripts.run_cycle3b_dsxl_ring import _kill_stale_qemu
        from gunnchos_device_os.device_lab.interactive_guest_four_games import (
            _guest_bash,
            _hot_patch_guest_agent,
        )
        from gunnchos_device_os.device_lab.interactive_guest_proofs import (
            _agent_call,
            _evidence_dir,
            _wait_agent,
            attempt_ring_app_mutation_pass,
            boot_interactive_guest,
        )
        from scripts.run_cycle3b_live_dsxl_ring_reearn import _push_weston
        from gunnchos_device_os.device_lab.current_pin_manifest import load_pin_manifest

        pin = load_pin_manifest(ROOT)
        out["pin_manifest_sha256"] = pin.get("manifest_sha256")
        _kill_stale_qemu()
        work = ROOT / "artifacts/wp011r/interactive_guest_session_ring"
        work.mkdir(parents=True, exist_ok=True)
        print(f"{LOG_PREFIX} boot", flush=True)
        boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=240, memory_mb=4096)
        session = boot.pop("_session", None)
        out["boot"] = {k: boot.get(k) for k in ("ok", "error", "pid") if k in boot}
        if session is None:
            out["blocker"] = "boot_failed"
            return 1
        fg = _agent_call(
            session, "file_get", path="/etc/hostname", offset=0, length=64, timeout_sec=10.0
        )
        if not (fg.get("ok") and fg.get("bytes_b64")):
            print(f"{LOG_PREFIX} hot_patch", _hot_patch_guest_agent(session, ROOT), flush=True)
            _wait_agent(session, tries=40, sleep_s=1.0)
        else:
            print(f"{LOG_PREFIX} hot_patch skipped file_get present", flush=True)
        print(f"{LOG_PREFIX} weston", _push_weston(session), flush=True)
        if not _wait_agent(session, tries=40, sleep_s=1.0):
            out["blocker"] = "agent_lost_after_weston"
            out["boot"] = {"ok": True, "error": "agent_lost_after_weston"}
            return 1
        for _ in range(30):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(1.0)
        _guest_bash(
            session,
            "set +e; test -d /root/pedestrian-pursuit && echo pp_ok; "
            "test -x /opt/gunnchos/bin/godot && /opt/gunnchos/bin/godot --version | head -1",
            timeout_sec=30,
            name="godot-probe",
        )
        # Soft wall-clock: mutation can hang >1h on virtio-serial; fail closed.
        print(f"{LOG_PREFIX} attempt deadline={1200}s", flush=True)
        ring_dir = _evidence_dir(ROOT, "ring")
        # Scrub stale Sep-7 evidence so PASS cannot be inherited.
        stale = ring_dir / "RING_APP_MUTATION_EVIDENCE.json"
        if stale.is_file():
            stale.rename(ring_dir / "RING_APP_MUTATION_EVIDENCE.stale_pre_current_pin.json")

        def _alarm(_signum, _frame):  # noqa: ARG001
            raise TimeoutError("ring_mutation_wall_clock_1200s")

        prev = signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(1200)
        try:
            ring = attempt_ring_app_mutation_pass(session, ring_dir)
        except TimeoutError as exc:
            ring = {
                "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
                "blocker": str(exc),
            }
            (ring_dir / "RING_APP_MUTATION_EVIDENCE.json").write_text(
                json.dumps(ring, indent=2) + "\n", encoding="utf-8"
            )
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, prev)
        out["ring"] = {
            k: ring.get(k)
            for k in (
                "RING_TO_REAL_APP_STATE_MUTATION_PASS",
                "note",
                "blocker",
                "mutation_marker",
            )
            if k in ring
        }
        out["RING_TO_REAL_APP_STATE_MUTATION_PASS"] = bool(
            ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
        )
        if not out["RING_TO_REAL_APP_STATE_MUTATION_PASS"]:
            out["blocker"] = ring.get("blocker") or ring.get("note") or "ring_attempt_failed"
        print(
            f"{LOG_PREFIX} result",
            out["RING_TO_REAL_APP_STATE_MUTATION_PASS"],
            out.get("blocker") or out.get("ring", {}).get("note"),
            flush=True,
        )
        return 0 if out["RING_TO_REAL_APP_STATE_MUTATION_PASS"] else 1
    except Exception as exc:  # noqa: BLE001
        out["blocker"] = f"exception:{exc}"[:500]
        print(f"{LOG_PREFIX} exception", exc, flush=True)
        return 1
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass
        out["elapsed_sec"] = round(time.time() - started, 1)
        out["finished_at_utc"] = _utc()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
