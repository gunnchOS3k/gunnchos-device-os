#!/usr/bin/env python3
"""Re-run ONLY failed/missing PRODUCT-USE-RC-002 legs on one COW-backed guest.

Preserves tip-current PASS evidence for G11 offline/quiz, G12/Dock, G13.
Fixes four-game call signature. Never second QEMU. Never delete sealed base.
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

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    attempt_dsxl_dual_compositor_pass,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_four_game_artifacts import prepare_owner_guest_staging  # noqa: E402
from gunnchos_device_os.device_lab.owner_four_game_guest import (  # noqa: E402
    attempt_owner_four_game_in_guest_pass,
)
from gunnchos_device_os.product_use.waike_guest_pack import write_guest_pack  # noqa: E402
from scripts.product_use_close_s1 import OUT, run_g14, run_g15, update_persona_table  # noqa: E402
from scripts.product_use_dock_reboot import reboot_update_recovery  # noqa: E402

RING_TIMEOUT_S = int(os.environ.get("PRODUCT_USE_RING_TIMEOUT_S", "240"))


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"{_utc()} {msg}", flush=True)


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def assert_no_qemu() -> None:
    try:
        out = subprocess.check_output(["pgrep", "-lf", "qemu-system-"], text=True).strip()
    except subprocess.CalledProcessError:
        return
    # Ignore self/command-line noise that merely mentions the string.
    lines = [
        ln
        for ln in out.splitlines()
        if "qemu-system-" in ln
        and "pgrep" not in ln
        and "product_use_rerun" not in ln
        and "assert_no_qemu" not in ln
        and "/bin/zsh" not in ln
    ]
    if lines:
        raise SystemExit("REFUSING_SECOND_QEMU still_running:\n" + "\n".join(lines))


def clean_poweroff(session: Any, work: Path) -> dict[str, Any]:
    pid_path = work / "qemu.pid"
    pid = int(pid_path.read_text().strip()) if pid_path.exists() else None
    try:
        _agent_call(
            session,
            "process_run",
            argv=["bash", "-lc", "sync; systemctl poweroff -i || poweroff"],
            timeout_sec=20.0,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f"poweroff agent err {exc}")
    mon = getattr(session, "monitor_sock", None)
    if mon:
        try:
            import socket

            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(str(mon))
            s.sendall(b"system_powerdown\n")
            s.close()
        except OSError:
            pass
    if not pid:
        return {"ok": False, "error": "no_pid"}
    for i in range(90):
        try:
            os.kill(pid, 0)
            time.sleep(1)
        except OSError:
            return {"ok": True, "exited": True, "wait_s": i}
    return {"ok": False, "exited": False, "error": "timeout_no_sigkill"}


def run_ring_child(work: Path) -> dict[str, Any]:
    ring_dir = OUT / "G11_ring"
    ring_dir.mkdir(parents=True, exist_ok=True)
    ring_ev = _evidence_dir(ROOT, "ring")
    marker = ring_dir / "_ring_child_result.json"
    if marker.exists():
        marker.unlink()
    child = f"""
import json, sys
from pathlib import Path
sys.path.insert(0, {str(ROOT)!r})
from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient
from gunnchos_device_os.device_lab.interactive_guest_proofs import attempt_ring_app_mutation_pass
from gunnchos_device_os.device_lab.virtualization.qemu_guest import QemuGuestSession
work = Path({str(work)!r})
sess = QemuGuestSession(work=work, profile={{'profile_id':'dsxl_coder'}}, repo_root=Path({str(ROOT)!r}))
sess.pid_file = work/'qemu.pid'
sess.boot_log = work/'qemu_boot.log'
mon = work/'qemu-monitor.sock'; ga = work/'guest-agent.sock'
sess.monitor_sock = mon.resolve() if mon.is_symlink() else mon
sess.virtio_serial_sock = ga.resolve() if ga.is_symlink() else ga
sess.agent = GuestAgentClient(sess.virtio_serial_sock, timeout_sec=15.0, extras={{'transport_preference':'virtio_serial'}})
sess.boot_complete = True
try:
  result = attempt_ring_app_mutation_pass(sess, Path({str(ring_ev)!r}))
except Exception as exc:
  result = {{'RING_TO_REAL_APP_STATE_MUTATION_PASS': False, 'ok': False, 'blocker': str(exc), 'RING_SPATIAL_ACCURACY': 'DIGITAL/SIMULATED'}}
Path({str(marker)!r}).write_text(json.dumps(result, default=str)+'\\n')
"""
    env = os.environ.copy()
    env.update({"PYTHONPATH": ".:src", "PYTHONUNBUFFERED": "1"})
    logf = open(OUT / "ring_rerun.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "-c", child],
        cwd=str(ROOT),
        env=env,
        stdout=logf,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        proc.wait(timeout=RING_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except OSError:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        result = {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
            "ok": False,
            "blocker": f"ring_timeout_after_{RING_TIMEOUT_S}s",
            "RING_SPATIAL_ACCURACY": "DIGITAL/SIMULATED",
            "observation_class": "DIGITAL/SIMULATED",
        }
    else:
        result = _load(marker) or {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": False,
            "ok": False,
            "blocker": f"ring_child_exit_{proc.returncode}",
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
    return result


def evaluate(results: dict[str, Any]) -> dict[str, Any]:
    g11 = _load(OUT / "G11_waike" / "result.json")
    g12 = _load(OUT / "G12_office" / "result.json")
    g13 = _load(OUT / "G13_teacher" / "result.json")
    dock = _load(OUT / "DOCK_CONTINUITY.json")
    ring = results.get("RING") or _load(OUT / "G11_ring" / "HONEST_REEARN_NOTE.json")
    g14 = results.get("G14") or {}
    g15 = results.get("G15") or {}
    reboot = results.get("REBOOT") or {}
    four = results.get("FOUR_GAME") or {}

    tokens = {
        "STUDENT_DIGITAL_PICKUP_AND_USE_READY": False,
        "OFFICE_DIGITAL_PICKUP_AND_USE_READY": False,
        "TEACHER_DIGITAL_PICKUP_AND_USE_READY": False,
        "BUILDER_DIGITAL_PICKUP_AND_USE_READY": False,
        "CREATIVE_DIGITAL_PICKUP_AND_USE_READY": False,
    }
    s1: list[str] = []
    # Student digital: HID quiz + real link_down offline + Ring PASS.
    # shipping_waike_product may remain false (fixture demotion) without blocking digital token.
    if g11.get("hid_quiz_submit") and (g11.get("offline") or {}).get("ok") and ring.get(
        "RING_TO_REAL_APP_STATE_MUTATION_PASS"
    ):
        tokens["STUDENT_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1.append("G11/Student: need HID quiz + link_down offline + Ring PASS")
    office_primary = bool(
        g12.get("office_primary_task_ok")
        or ((g12.get("primary_task") or {}).get("ok") if isinstance(g12.get("primary_task"), dict) else False)
    )
    if (g12.get("ok") or dock.get("ok")) and reboot.get("ok") and office_primary:
        tokens["OFFICE_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1.append("G12/Office: need dock+reboot+LibreOffice edit/save primary-task")
    # Teacher digital: fixture ACL + FS hygiene. REAL_TEACHER_E6 stays false (S2 residual).
    if g13.get("ok") and g13.get("role_acl_ok") and g13.get("fs_hygiene_ok", True):
        tokens["TEACHER_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1.append("G13/Teacher: digital ACL/FS hygiene incomplete")
    if four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") and g14.get("ok"):
        tokens["BUILDER_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1.append("G14/Builder: need four-game PASS + DSXL/builder ok")
    if g15.get("ok"):
        tokens["CREATIVE_DIGITAL_PICKUP_AND_USE_READY"] = True
    else:
        s1.append("G15 creative PNG not earned")
    return {"tokens": tokens, "S0_open": 0, "S1_open": s1}


def main() -> int:
    started = _utc()
    assert_no_qemu()
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = "rc002"
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

    inventory = {
        "G11": _load(OUT / "G11_waike" / "result.json"),
        "G12": _load(OUT / "G12_office" / "result.json"),
        "DOCK": _load(OUT / "DOCK_CONTINUITY.json"),
        "G13": _load(OUT / "G13_teacher" / "result.json"),
        "RING_prior": _load(OUT / "G11_ring" / "HONEST_REEARN_NOTE.json"),
    }
    _log(
        "KEEP "
        f"G11 quiz={inventory['G11'].get('hid_quiz_submit')} offline={(inventory['G11'].get('offline') or {}).get('ok')} "
        f"G12={inventory['G12'].get('ok')} DOCK={inventory['DOCK'].get('ok')} G13={inventory['G13'].get('ok')}"
    )

    staging = prepare_owner_guest_staging(ROOT)
    _log(f"staging_ok={staging.get('ok')}")
    if not staging.get("ok"):
        (OUT / "FOUR_GAME").mkdir(parents=True, exist_ok=True)
        (OUT / "FOUR_GAME" / "result.json").write_text(
            json.dumps({"ok": False, "blocker": "staging_failed", "staging": staging}, indent=2)
            + "\n"
        )

    work = ROOT / "artifacts/product_use/interactive_guest_session_rerun"
    if work.exists():
        # keep edk2 vars if present; clear stale pid
        for name in ("qemu.pid", "qemu_boot.log"):
            p = work / name
            if p.exists() or p.is_symlink():
                try:
                    p.unlink()
                except OSError:
                    pass
    work.mkdir(parents=True, exist_ok=True)
    tmpl = Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd")
    if tmpl.is_file() and not (work / "edk2-aarch64-vars.fd").exists():
        shutil.copyfile(tmpl, work / "edk2-aarch64-vars.fd")

    boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=300, memory_mb=3072)
    session = boot.pop("_session", None)
    results: dict[str, Any] = {}
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_002.rerun_failed.v1",
        "started_at_utc": started,
        "boot_ok": bool(boot.get("ok")),
        "kept": {
            "G11_hid_quiz": inventory["G11"].get("hid_quiz_submit"),
            "G11_offline": (inventory["G11"].get("offline") or {}).get("ok"),
            "G12": inventory["G12"].get("ok"),
            "DOCK": inventory["DOCK"].get("ok"),
            "G13": inventory["G13"].get("ok"),
        },
        "rerun": ["G15", "G14", "REBOOT", "RING", "FOUR_GAME"],
    }
    if not boot.get("ok") or session is None:
        summary["error"] = boot.get("error") or "boot_failed"
        (OUT / "RERUN_FAILED_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 1

    try:
        for _ in range(30):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2)

        _log("G15")
        results["G15"] = run_g15(session)
        (OUT / "G15_creative").mkdir(parents=True, exist_ok=True)
        (OUT / "G15_creative" / "result.json").write_text(
            json.dumps(results["G15"], indent=2, default=str) + "\n"
        )
        _log(f"G15 ok={results['G15'].get('ok')} app={results['G15'].get('app')}")

        _log("G14")
        g14_dir = OUT / "G14_dsxl_s1"
        g14_dir.mkdir(parents=True, exist_ok=True)
        results["G14"] = run_g14(session, g14_dir)
        results["G14"]["dsxl"] = attempt_dsxl_dual_compositor_pass(session, g14_dir)
        (g14_dir / "result.json").write_text(
            json.dumps(results["G14"], indent=2, default=str) + "\n"
        )
        _log(
            f"G14 ok={results['G14'].get('ok')} dsxl={((results['G14'].get('dsxl') or {}).get('DSXL_DUAL_COMPOSITOR_UX_PASS'))}"
        )

        _log("REBOOT")
        results["REBOOT"] = reboot_update_recovery(session)
        (OUT / "REBOOT_UPDATE_RECOVERY.json").write_text(
            json.dumps(results["REBOOT"], indent=2, default=str) + "\n"
        )
        _log(f"REBOOT ok={results['REBOOT'].get('ok')}")

        _log("RING")
        results["RING"] = run_ring_child(work)
        _log(
            f"RING pass={results['RING'].get('RING_TO_REAL_APP_STATE_MUTATION_PASS')} "
            f"blocker={results['RING'].get('blocker')}"
        )

        # Merge kept + new for persona table
        merge = {
            "G11": inventory["G11"],
            "G12": inventory["G12"],
            "G13": inventory["G13"],
            "G14": results["G14"],
            "G15": results["G15"],
            "RING": results["RING"],
            "DOCK": inventory["DOCK"],
        }
        update_persona_table(merge)

        power = clean_poweroff(session, work)
        summary["poweroff"] = power
        _log(f"poweroff {power}")

        if power.get("exited") and staging.get("ok"):
            assert_no_qemu()
            _log("FOUR_GAME")
            os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging.get("staging"))
            four_work = ROOT / "artifacts/wp011r/interactive_guest_session_four"
            four_work.mkdir(parents=True, exist_ok=True)
            if tmpl.is_file():
                shutil.copyfile(tmpl, four_work / "edk2-aarch64-vars.fd")
            boot2 = boot_interactive_guest(
                ROOT, four_work, dual=True, boot_timeout_s=300, memory_mb=3072
            )
            sess2 = boot2.pop("_session", None)
            if not boot2.get("ok") or sess2 is None:
                results["FOUR_GAME"] = {"ok": False, "boot": boot2, "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False}
            else:
                try:
                    for _ in range(40):
                        if _agent_call(sess2, "compositor_info", timeout_sec=10.0).get("available"):
                            break
                        time.sleep(2)
                    evid = _evidence_dir(ROOT, "games")
                    results["FOUR_GAME"] = attempt_owner_four_game_in_guest_pass(sess2, ROOT, evid)
                finally:
                    clean_poweroff(sess2, four_work)
            (OUT / "FOUR_GAME").mkdir(parents=True, exist_ok=True)
            (OUT / "FOUR_GAME" / "result.json").write_text(
                json.dumps(results["FOUR_GAME"], indent=2, default=str) + "\n"
            )
            fg = ROOT / "artifacts/wp011r/games/four_games_in_guest.json"
            if fg.exists():
                shutil.copy2(fg, OUT / "FOUR_GAME" / "four_games_in_guest.json")
            _log(
                f"FOUR_GAME pass={results['FOUR_GAME'].get('FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS')} "
                f"blocker={results['FOUR_GAME'].get('blocker')}"
            )
        else:
            results["FOUR_GAME"] = {
                "ok": False,
                "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
                "blocker": "poweroff_or_staging_blocked",
                "poweroff": power,
                "staging_ok": staging.get("ok"),
            }

        tok = evaluate(results)
        tip = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        summary.update(
            {
                "finished_at_utc": _utc(),
                "tip": tip,
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
                        "app": (v or {}).get("app"),
                    }
                    for k, v in results.items()
                },
                "persona_tokens": tok["tokens"],
                "S0_open": tok["S0_open"],
                "S1_open": tok["S1_open"],
                "READY_FOR_INDEPENDENT_VERIFIER": True,
                "READY_FOR_EDMUND_MERGE": False,
                "cursor_never_merges": True,
            }
        )
        (OUT / "RERUN_FAILED_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
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
            "kept_legs": summary["kept"],
            "READY_FOR_INDEPENDENT_VERIFIER": True,
            "READY_FOR_EDMUND_MERGE": False,
            "cursor_never_merges": True,
            "prefer_fail_over_false_pass": True,
        }
        (ROOT / "artifacts/product_use/PRODUCT_USE_RC_002_STATUS.json").write_text(
            json.dumps(status, indent=2) + "\n"
        )
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 0
    except Exception as exc:  # noqa: BLE001
        summary["error"] = str(exc)
        summary["partial"] = {k: (v or {}).get("ok") for k, v in results.items()}
        summary["finished_at_utc"] = _utc()
        (OUT / "RERUN_FAILED_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
