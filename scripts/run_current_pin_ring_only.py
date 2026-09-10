#!/usr/bin/env python3
"""Current-pin RING-only re-earn with fail-closed wall clock.

Do not compete for the guest-agent socket from other processes while this runs.

Wall-clock uses multiprocessing terminate/kill (not SIGALRM) because AF_UNIX
I/O on some Python builds does not reliably deliver SIGALRM mid-recv/send.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "artifacts/device_lab_current_pin/RING_REEARN.json"
LOG_PREFIX = "RING_ONLY"
WALL_CLOCK_SEC = 1200


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sync_gaps_ring_token(*, ring_pass: bool, blocker: str | None) -> None:
    """Keep WP-011R gaps register consistent with RING evidence (CI gate)."""
    gaps_path = ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json"
    if not gaps_path.is_file():
        return
    try:
        gaps = json.loads(gaps_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    pt = gaps.setdefault("pass_tokens", {})
    pt["RING_TO_REAL_APP_STATE_MUTATION_PASS"] = bool(ring_pass)
    for g in gaps.get("gaps") or []:
        if g.get("token") != "RING_TO_REAL_APP_STATE_MUTATION_PASS":
            continue
        if ring_pass:
            g["status"] = "EARNED"
            g["earned"] = True
            g["pass"] = True
            g["digital_earned"] = True
            g["summary"] = "EARNED: current-pin Ring re-earn on Interactive Guest"
        else:
            g["status"] = "OPEN_CURRENT_PIN_REEARN"
            g["earned"] = False
            g["pass"] = False
            g["digital_earned"] = False
            g["summary"] = f"OPEN: {blocker or 'ring_attempt_failed'}"
    gaps["updated_at_utc"] = _utc()
    gaps_path.write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")


def _mutation_worker(result_path: str) -> None:
    """Child process: boot guest + attempt mutation; write JSON result path."""
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    # Allow guest→host HTTP (10.0.2.2) so Godot 4.5 can be fetched without a
    # flaky 126MB virtio-serial file_put. Lab isolation remains non-shipping.
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")
    os.environ.setdefault("GUNNCH_RING_SKIP_VIRTIO_PP_PUT", "1")
    started = time.time()
    out: dict = {
        "schema": "gunnchos.device_lab.current_pin.ring_reearn.v1",
        "started_at_utc": _utc(),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
        "worker_pid": os.getpid(),
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
            return
        out["qemu_pid"] = getattr(session, "pid", None) or boot.get("pid")
        out["guest_agent_sock"] = str(getattr(session, "virtio_serial_sock", "") or "")
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
            return
        for _ in range(30):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(1.0)
        # Prove a harmless guest-agent command before mutation.
        baseline = _agent_call(session, "ping", timeout_sec=8.0)
        out["pre_mutation_baseline"] = {
            "ping_ok": bool(baseline.get("ok") and baseline.get("pong")),
            "transport": baseline.get("transport"),
            "error": baseline.get("error"),
            "error_class": baseline.get("error_class"),
            "t_utc": _utc(),
        }
        print(f"{LOG_PREFIX} baseline_ping", out["pre_mutation_baseline"], flush=True)
        if not out["pre_mutation_baseline"]["ping_ok"]:
            out["blocker"] = "pre_mutation_baseline_ping_failed"
            return
        _guest_bash(
            session,
            "set +e; test -d /root/pedestrian-pursuit && echo pp_ok; "
            "test -x /opt/gunnchos/bin/godot && /opt/gunnchos/bin/godot --version | head -1",
            timeout_sec=30,
            name="godot-probe",
        )
        print(f"{LOG_PREFIX} attempt deadline={WALL_CLOCK_SEC}s", flush=True)
        ring_dir = _evidence_dir(ROOT, "ring")
        # Scrub stale Sep-7 evidence so PASS cannot be inherited.
        stale = ring_dir / "RING_APP_MUTATION_EVIDENCE.json"
        if stale.is_file():
            stale.rename(ring_dir / "RING_APP_MUTATION_EVIDENCE.stale_pre_current_pin.json")

        ring = attempt_ring_app_mutation_pass(session, ring_dir)
        out["ring"] = {
            k: ring.get(k)
            for k in (
                "RING_TO_REAL_APP_STATE_MUTATION_PASS",
                "note",
                "blocker",
                "mutation_marker",
                "correlation_id",
            )
            if k in ring
        }
        out["correlation_id"] = ring.get("correlation_id")
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
    except Exception as exc:  # noqa: BLE001
        out["blocker"] = f"exception:{exc}"[:500]
        print(f"{LOG_PREFIX} exception", exc, flush=True)
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass
        out["elapsed_sec"] = round(time.time() - started, 1)
        out["finished_at_utc"] = _utc()
        Path(result_path).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(out, indent=2), flush=True)


def main() -> int:
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")
    os.environ.setdefault("GUNNCH_RING_SKIP_VIRTIO_PP_PUT", "1")
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    worker_out = OUT.parent / "RING_REEARN_WORKER.json"
    if worker_out.exists():
        worker_out.unlink()

    ctx = mp.get_context("spawn")
    proc = ctx.Process(target=_mutation_worker, args=(str(worker_out),), name="ring-reearn-worker")
    proc.start()
    print(f"{LOG_PREFIX} worker_pid={proc.pid} wall_clock={WALL_CLOCK_SEC}s", flush=True)
    proc.join(WALL_CLOCK_SEC + 30)
    out: dict
    if proc.is_alive():
        print(f"{LOG_PREFIX} wall_clock_exceeded terminating worker", flush=True)
        proc.terminate()
        proc.join(15)
        if proc.is_alive():
            proc.kill()
            proc.join(5)
        # Preserve any stage heartbeat written before kill.
        heartbeat = ROOT / "artifacts/wp011r/ring/RING_STAGE_HEARTBEAT.json"
        waterfall = ROOT / "artifacts/wp011r/ring/RING_STAGE_WATERFALL.jsonl"
        last_stage = None
        if heartbeat.is_file():
            try:
                last_stage = json.loads(heartbeat.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                last_stage = {"raw": heartbeat.read_text(encoding="utf-8")[:500]}
        out = {
            "schema": "gunnchos.device_lab.current_pin.ring_reearn.v1",
            "started_at_utc": _utc(),
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
            "blocker": "ring_mutation_hung_virtio_serial_wall_clock_killed",
            "note": (
                "Worker exceeded wall clock; terminated via multiprocessing "
                "(not SIGALRM). Timeout is not PASS."
            ),
            "last_stage_heartbeat": last_stage,
            "waterfall_path": str(waterfall) if waterfall.is_file() else None,
            "worker_exitcode": proc.exitcode,
            "elapsed_sec": round(time.time() - started, 1),
            "finished_at_utc": _utc(),
        }
        # Fail-closed evidence so CI token sync stays honest.
        ring_dir = ROOT / "artifacts/wp011r/ring"
        ring_dir.mkdir(parents=True, exist_ok=True)
        evid = {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
            "blocker": out["blocker"],
            "generated_at_utc": _utc(),
            "last_stage_heartbeat": last_stage,
            "correlation_id": (last_stage or {}).get("correlation_id"),
        }
        (ring_dir / "RING_APP_MUTATION_EVIDENCE.json").write_text(
            json.dumps(evid, indent=2) + "\n", encoding="utf-8"
        )
    elif worker_out.is_file():
        out = json.loads(worker_out.read_text(encoding="utf-8"))
    else:
        out = {
            "schema": "gunnchos.device_lab.current_pin.ring_reearn.v1",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
            "blocker": f"worker_exited_without_result_exitcode={proc.exitcode}",
            "elapsed_sec": round(time.time() - started, 1),
            "finished_at_utc": _utc(),
        }

    ring_pass = bool(out.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"))
    _sync_gaps_ring_token(ring_pass=ring_pass, blocker=out.get("blocker"))
    gate = {
        "generated_at_utc": _utc(),
        "pin_manifest_sha256": out.get("pin_manifest_sha256"),
        "RING_TO_REAL_APP_STATE_MUTATION_PASS": ring_pass,
        "verdict": "PASS" if ring_pass else "FAIL",
        "blocker": None if ring_pass else out.get("blocker"),
        "evidence": "artifacts/device_lab_current_pin/RING_REEARN.json",
        "correlation_id": out.get("correlation_id"),
    }
    (OUT.parent / "RING_TO_REAL_APP_STATE_MUTATION_PASS.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2), flush=True)
    return 0 if ring_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
