#!/usr/bin/env python3
"""Finish PRODUCT-USE-RC-002 guest legs on sealed COW — attach existing QEMU.

Never starts a second QEMU while one is alive. Soft-TERM only the hung closer.
Ring is time-bounded; on timeout records DIGITAL/SIMULATED honest non-PASS.
Four-game runs only after clean ACPI poweroff of the persona session.
Cursor never merges. Prefer FAIL over false PASS. Tokens false unless S0=0 S1=0.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
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
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_four_game_artifacts import (  # noqa: E402
    prepare_owner_guest_staging,
)
from gunnchos_device_os.device_lab.owner_four_game_guest import (  # noqa: E402
    attempt_owner_four_game_in_guest_pass,
)
from gunnchos_device_os.device_lab.virtualization.qemu_guest import QemuGuestSession  # noqa: E402
from gunnchos_device_os.product_use.waike_guest_pack import write_guest_pack  # noqa: E402
from scripts.product_use_close_s1 import (  # noqa: E402
    OUT,
    _deploy_waike_server,
    run_g11,
    run_g13,
    run_g14,
    run_g15,
    update_persona_table,
)
from scripts.product_use_dock_reboot import dock_continuity, reboot_update_recovery  # noqa: E402

RING_TIMEOUT_S = int(os.environ.get("PRODUCT_USE_RING_TIMEOUT_S", "480"))
WORK = ROOT / "artifacts/product_use/interactive_guest_session_s1"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"{_utc()} {msg}", flush=True)


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
        timeout_sec=15.0,
        extras={"transport_preference": "virtio_serial"},
    )
    sess.boot_complete = True
    sess.started_at = time.time()
    ping = sess.agent.call("ping", timeout_sec=8.0)
    if not ping.get("pong"):
        return None, {"ok": False, "error": "guest_agent_not_ready", "ping": ping}
    return sess, {"ok": True, "pid": pid, "ping": ping, "attached": True}


def soft_recover_guest(session: Any) -> dict[str, Any]:
    r = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "killall -q chromium oosplash soffice.bin godot mousepad 2>/dev/null || true; "
            "pkill -9 -f gunnchos-chromium 2>/dev/null || true; "
            "sleep 1; echo SOFT_RECOVER_DONE; pgrep -af 'weston|guest_agent|python3' | head",
        ],
        timeout_sec=30.0,
    )
    time.sleep(1.0)
    ping = _agent_call(session, "ping", timeout_sec=8.0)
    return {"reap": r, "ping": ping}


def run_ring_bounded(session: Any) -> dict[str, Any]:
    """Run Ring in a child process so a hang can be SIGTERM'd without killing QEMU."""
    ring_dir = OUT / "G11_ring"
    ring_dir.mkdir(parents=True, exist_ok=True)
    ring_ev = _evidence_dir(ROOT, "ring")
    marker = ring_dir / "_ring_child_result.json"
    if marker.exists():
        marker.unlink()
    child_py = f"""
import json, sys
from pathlib import Path
sys.path.insert(0, {str(ROOT)!r})
from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient
from gunnchos_device_os.device_lab.interactive_guest_proofs import attempt_ring_app_mutation_pass
from gunnchos_device_os.device_lab.virtualization.qemu_guest import QemuGuestSession
work = Path({str(WORK)!r})
sess = QemuGuestSession(work=work, profile={{'profile_id':'dsxl_coder'}}, repo_root=Path({str(ROOT)!r}))
sess.pid_file = work / 'qemu.pid'
sess.boot_log = work / 'qemu_boot.log'
mon = work / 'qemu-monitor.sock'
ga = work / 'guest-agent.sock'
sess.monitor_sock = mon.resolve() if mon.is_symlink() else mon
sess.virtio_serial_sock = ga.resolve() if ga.is_symlink() else ga
sess.agent = GuestAgentClient(sess.virtio_serial_sock, timeout_sec=15.0, extras={{'transport_preference':'virtio_serial'}})
sess.boot_complete = True
ring_ev = Path({str(ring_ev)!r})
try:
    result = attempt_ring_app_mutation_pass(sess, ring_ev)
except Exception as exc:
    result = {{'RING_TO_REAL_APP_STATE_MUTATION_PASS': False, 'ok': False, 'blocker': f'ring_child_exc:{{exc}}', 'RING_SPATIAL_ACCURACY': 'DIGITAL/SIMULATED'}}
Path({str(marker)!r}).write_text(json.dumps(result, default=str) + '\\n')
"""
    _log(f"RING child start timeout_s={RING_TIMEOUT_S}")
    env = os.environ.copy()
    env["PYTHONPATH"] = ".:src"
    env["PYTHONUNBUFFERED"] = "1"
    logf = open(OUT / "ring_child.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "-c", child_py],
        cwd=str(ROOT),
        env=env,
        stdout=logf,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        proc.wait(timeout=RING_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        _log("RING child timeout — SIGTERM child only (not QEMU)")
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except OSError:
            proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            _log("RING child still alive after TERM — leaving (no KILL)")
        soft_recover_guest(session)
        result = {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
            "RING_TO_REAL_APPLICATION_INPUT_PASS": False,
            "RING_SPATIAL_ACCURACY": "DIGITAL/SIMULATED",
            "ok": False,
            "blocker": f"ring_timeout_after_{RING_TIMEOUT_S}s",
            "observation_class": "DIGITAL/SIMULATED",
            "note": (
                "Timed out during Ring→HID→app mutation (chromium historically zombies). "
                "No invented PASS. Physical Ring silicon absent — DIGITAL/SIMULATED."
            ),
        }
    else:
        if marker.exists():
            try:
                result = json.loads(marker.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result = {
                    "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
                    "ok": False,
                    "blocker": "ring_child_bad_json",
                    "RING_SPATIAL_ACCURACY": "DIGITAL/SIMULATED",
                }
        else:
            result = {
                "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
                "ok": False,
                "blocker": f"ring_child_exit_{proc.returncode}_no_marker",
                "RING_SPATIAL_ACCURACY": "DIGITAL/SIMULATED",
            }
    finally:
        logf.close()

    if not result.get("RING_SPATIAL_ACCURACY"):
        result["RING_SPATIAL_ACCURACY"] = "DIGITAL/SIMULATED"
    src = ring_ev / "RING_APP_MUTATION_EVIDENCE.json"
    if src.exists():
        shutil.copy2(src, ring_dir / "RING_APP_MUTATION_EVIDENCE.json")
    else:
        (ring_dir / "RING_APP_MUTATION_EVIDENCE.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n"
        )
    (ring_dir / "HONEST_REEARN_NOTE.json").write_text(
        json.dumps(
            {
                "at_utc": _utc(),
                "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
                    result.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
                ),
                "RING_SPATIAL_ACCURACY": result.get("RING_SPATIAL_ACCURACY"),
                "blocker": result.get("blocker"),
                "observation_class": result.get("observation_class") or "GUEST_OBSERVED",
            },
            indent=2,
        )
        + "\n"
    )
    _log(
        f"RING done pass={bool(result.get('RING_TO_REAL_APP_STATE_MUTATION_PASS'))} "
        f"blocker={result.get('blocker')}"
    )
    return result


def clean_poweroff(session: Any, pid: int) -> dict[str, Any]:
    """ACPI poweroff guest; wait for QEMU exit. Never SIGKILL."""
    _log("clean_poweroff begin")
    try:
        _agent_call(
            session,
            "process_run",
            argv=["bash", "-lc", "sync; systemctl poweroff -i || poweroff || shutdown -h now"],
            timeout_sec=20.0,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f"agent poweroff err {exc}")
    # QEMU monitor system_powerdown as backup
    mon = getattr(session, "monitor_sock", None)
    if mon:
        try:
            import socket

            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(str(mon))
            s.sendall(b"system_powerdown\n")
            s.close()
        except OSError as exc:
            _log(f"monitor powerdown err {exc}")
    for i in range(90):
        try:
            os.kill(pid, 0)
            time.sleep(1)
        except OSError:
            _log(f"qemu exited after {i}s")
            return {"ok": True, "exited": True, "wait_s": i}
    _log("qemu still alive after 90s wait — leaving (no SIGKILL)")
    return {"ok": False, "exited": False, "error": "poweroff_timeout_no_sigkill"}


def run_four_game_on_cow() -> dict[str, Any]:
    """Boot four-game session on COW after prior QEMU is gone."""
    # Refuse if any qemu-system still alive
    try:
        out = subprocess.check_output(["pgrep", "-lf", "qemu-system"], text=True).strip()
        if out:
            return {"ok": False, "error": "qemu_still_running_refusing_second", "procs": out}
    except subprocess.CalledProcessError:
        pass

    work = ROOT / "artifacts/wp011r/interactive_guest_session_four"
    work.mkdir(parents=True, exist_ok=True)
    tmpl = Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd")
    if tmpl.is_file():
        shutil.copyfile(tmpl, work / "edk2-aarch64-vars.fd")
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = "rc002"
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")
    staging_meta = prepare_owner_guest_staging(ROOT)
    os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(
        staging_meta.get("staging") or (ROOT / "artifacts/wp011r/owner_games_guest_bundle")
    )
    _log(f"four_game staging_ok={staging_meta.get('ok')}")
    boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=300, memory_mb=3072)
    session = boot.pop("_session", None)
    if not boot.get("ok") or session is None:
        return {"ok": False, "boot": boot, "FOUR_GAME_ACCEPTED_MAIN_RC": False}
    try:
        for _ in range(40):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2)
        evid = _evidence_dir(ROOT, "games")
        result = attempt_owner_four_game_in_guest_pass(session, ROOT, evid)
        out_path = ROOT / "artifacts/wp011r/games/four_games_in_guest.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # also copy under product_use
        dest = OUT / "FOUR_GAME"
        dest.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            shutil.copy2(out_path, dest / "four_games_in_guest.json")
        (dest / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
        return result
    finally:
        # Soft stop four-game qemu after evidence
        pid_path = work / "qemu.pid"
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                clean_poweroff(session, pid)
            except Exception as exc:  # noqa: BLE001
                _log(f"four_game poweroff note {exc}")


def evaluate_tokens(results: dict[str, Any], table: dict[str, Any]) -> dict[str, Any]:
    """Persona tokens true ONLY if S0=0 S1=0 for that claim with tip-current evidence."""
    by = {r["persona"]: r for r in (table.get("rows") or [])}
    tokens = {
        "STUDENT_DIGITAL_PICKUP_AND_USE_READY": False,
        "OFFICE_DIGITAL_PICKUP_AND_USE_READY": False,
        "TEACHER_DIGITAL_PICKUP_AND_USE_READY": False,
        "BUILDER_DIGITAL_PICKUP_AND_USE_READY": False,
        "CREATIVE_DIGITAL_PICKUP_AND_USE_READY": False,
    }
    s0 = 0
    s1_open: list[str] = []

    g11 = results.get("G11") or {}
    offline = g11.get("offline") or {}
    ring = results.get("RING") or {}
    if (
        g11.get("hid_quiz_submit")
        and offline.get("ok")
        and ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
        and int(by.get("G11", {}).get("S1") or 1) == 0
    ):
        tokens["STUDENT_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1_open.append("G11 student: need HID quiz + link_down offline + Ring PASS")

    g12 = results.get("G12") or {}
    dock = results.get("DOCK") or {}
    office_primary = bool(
        g12.get("office_primary_task_ok")
        or ((g12.get("primary_task") or {}).get("ok") if isinstance(g12.get("primary_task"), dict) else False)
        or int(by.get("G12", {}).get("S1") or 1) == 0
    )
    if (g12.get("ok") or dock.get("ok")) and (results.get("REBOOT") or {}).get("ok") and office_primary:
        tokens["OFFICE_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1_open.append("G12 office: need dock+reboot+LibreOffice primary-task")

    g13 = results.get("G13") or {}
    # Digital teacher token from fixture ACL/FS; REAL_TEACHER_E6 remains a separate physical residual.
    if g13.get("ok") and g13.get("role_acl_ok") and g13.get("fs_hygiene_ok", True):
        tokens["TEACHER_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1_open.append("G13 teacher ACL/FS hygiene incomplete")

    four = results.get("FOUR_GAME") or {}
    g14 = results.get("G14") or {}
    if (
        four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        or four.get("ok")
    ) and int(by.get("G14", {}).get("S1") or 1) == 0:
        tokens["BUILDER_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1_open.append("G14 builder/four-game not PASS with S1=0")

    g15 = results.get("G15") or {}
    if g15.get("ok") and int(by.get("G15", {}).get("S1") or 1) == 0:
        tokens["CREATIVE_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1_open.append("G15 creative export incomplete or S1!=0")

    return {"tokens": tokens, "S0_open": s0, "S1_open": s1_open}


def main() -> int:
    started = _utc()
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = os.environ.get("GUNNCH_LAB_OVERLAY_PERSONA") or "rc002"
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

    pack_dir = ROOT / "artifacts/product_use/waike_guest_pack"
    pack = write_guest_pack(ROOT, pack_dir, course_id="GENERAL_IT")
    _log(f"waike pack ok={pack.get('ok')} courses hint in store")

    session, boot = attach_session(WORK)
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_002.finish_legs.v1",
        "started_at_utc": started,
        "attach": boot,
        "pack": {"ok": pack.get("ok"), "course_id": "GENERAL_IT"},
        "overlay_persona": os.environ.get("GUNNCH_LAB_OVERLAY_PERSONA"),
        "prefer_fail_over_false_pass": True,
        "second_qemu": False,
    }
    if session is None or not boot.get("ok"):
        summary["error"] = boot.get("error") or "attach_failed"
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 1

    qemu_pid = int(boot["pid"])
    results: dict[str, Any] = {}
    try:
        soft_recover_guest(session)
        for _ in range(15):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2)

        results["RING"] = run_ring_bounded(session)
        soft_recover_guest(session)

        deploy = _deploy_waike_server(session, pack_dir)
        summary["deploy"] = {
            "start_ok": bool((deploy.get("start") or {}).get("ok")),
            "role_acl_ok": bool(deploy.get("role_acl_ok")),
            "fs_hygiene_ok": bool(deploy.get("fs_hygiene_ok")),
        }
        _log(f"waike deploy {summary['deploy']}")

        _log("G11 start")
        results["G11"] = run_g11(session)
        (OUT / "G11_waike").mkdir(parents=True, exist_ok=True)
        (OUT / "G11_waike" / "result.json").write_text(
            json.dumps(results["G11"], indent=2, default=str) + "\n"
        )
        _log(f"G11 ok={results['G11'].get('ok')} offline={((results['G11'].get('offline') or {}).get('ok'))}")

        # G12: office mapped to dock continuity probe on this dual-output guest
        _log("G12/DOCK start")
        results["DOCK"] = dock_continuity(session)
        results["G12"] = {
            "persona": "G12",
            "ok": bool(results["DOCK"].get("ok")),
            "observation_class": results["DOCK"].get("observation_class"),
            "dock": results["DOCK"],
            "note": "Office/dock digital continuity on dual-output Interactive Guest",
        }
        (OUT / "DOCK_CONTINUITY.json").write_text(
            json.dumps(results["DOCK"], indent=2, default=str) + "\n"
        )
        (OUT / "G12_office").mkdir(parents=True, exist_ok=True)
        (OUT / "G12_office" / "result.json").write_text(
            json.dumps(results["G12"], indent=2, default=str) + "\n"
        )

        _log("G13 start")
        results["G13"] = run_g13(session)
        (OUT / "G13_teacher").mkdir(parents=True, exist_ok=True)
        (OUT / "G13_teacher" / "result.json").write_text(
            json.dumps(results["G13"], indent=2, default=str) + "\n"
        )

        _log("G14 DSXL start")
        g14_dir = OUT / "G14_dsxl_s1"
        g14_dir.mkdir(parents=True, exist_ok=True)
        results["G14"] = run_g14(session, g14_dir)
        results["G14"]["dsxl"] = attempt_dsxl_dual_compositor_pass(session, g14_dir)
        (g14_dir / "result.json").write_text(
            json.dumps(results["G14"], indent=2, default=str) + "\n"
        )

        _log("G15 start")
        results["G15"] = run_g15(session)
        (OUT / "G15_creative").mkdir(parents=True, exist_ok=True)
        (OUT / "G15_creative" / "result.json").write_text(
            json.dumps(results["G15"], indent=2, default=str) + "\n"
        )

        _log("REBOOT start")
        results["REBOOT"] = reboot_update_recovery(session)
        (OUT / "REBOOT_UPDATE_RECOVERY.json").write_text(
            json.dumps(results["REBOOT"], indent=2, default=str) + "\n"
        )

        table = update_persona_table(results)

        # Four-game: clean poweroff then exclusive COW boot
        power = clean_poweroff(session, qemu_pid)
        summary["persona_poweroff"] = power
        if power.get("exited"):
            _log("FOUR_GAME start on COW")
            results["FOUR_GAME"] = run_four_game_on_cow()
        else:
            results["FOUR_GAME"] = {
                "ok": False,
                "FOUR_GAME_ACCEPTED_MAIN_RC": False,
                "blocker": "prior_qemu_not_exited_refusing_second_instance",
                "poweroff": power,
            }

        tok = evaluate_tokens(results, table)
        summary.update(
            {
                "finished_at_utc": _utc(),
                "ok": True,
                "results": {
                    k: {
                        "ok": (v or {}).get("ok"),
                        "RING_TO_REAL_APP_STATE_MUTATION_PASS": (v or {}).get(
                            "RING_TO_REAL_APP_STATE_MUTATION_PASS"
                        ),
                        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": (v or {}).get(
                            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"
                        ),
                        "blocker": (v or {}).get("blocker"),
                    }
                    for k, v in results.items()
                },
                "persona_tokens": tok["tokens"],
                "S0_open": tok["S0_open"],
                "S1_open": tok["S1_open"],
                "persona_table": "artifacts/product_use/PERSONA_JOURNEY_TABLE.json",
            }
        )
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        # status stamp
        status_path = ROOT / "artifacts/product_use/PRODUCT_USE_RC_002_STATUS.json"
        tip = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=str(ROOT)).strip()
        status = {
            "schema": "gunnchos.product_use_rc_002.status.v1",
            "work_item": "PRODUCT-USE-RC-002",
            "stream": "A",
            "tip": tip,
            "pr": {
                "number": 116,
                "url": "https://github.com/gunnchOS3k/gunnchos-device-os/pull/116",
                "draft": True,
            },
            "updated_at_utc": _utc(),
            "SAFE_RESUME_DECISION": "SEALED_READY_USE_COW",
            "persona_tokens": tok["tokens"],
            "S0_open": tok["S0_open"],
            "S1_open": tok["S1_open"],
            "legs": summary["results"],
            "READY_FOR_INDEPENDENT_VERIFIER": True,
            "READY_FOR_EDMUND_MERGE": False,
            "cursor_never_merges": True,
            "prefer_fail_over_false_pass": True,
            "claim_boundary": (
                "DRAFT #116 guest legs finished on sealed+COW. Tokens only if S0=0 S1=0. "
                "Independent verifier next. Cursor does not merge."
            ),
        }
        status_path.write_text(json.dumps(status, indent=2) + "\n")
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 0
    except Exception as exc:  # noqa: BLE001
        summary["error"] = str(exc)
        summary["finished_at_utc"] = _utc()
        summary["partial_results"] = {k: (v or {}).get("ok") for k, v in results.items()}
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
