#!/usr/bin/env python3
"""Attach to existing COW QEMU and finish open PRODUCT-USE-RC-002 legs.

Does NOT start a second QEMU while one is alive. After clean poweroff, boots
one FOUR_GAME guest. Prefer FAIL over invented PASS.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PRODUCT_USE_RING_TIMEOUT_S", "600")

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
from scripts.product_use_attach_s1_continue import attach_session  # noqa: E402
from scripts.product_use_close_s1 import OUT, run_g14, update_persona_table  # noqa: E402
from scripts.product_use_rerun_failed_legs import (  # noqa: E402
    assert_no_qemu,
    clean_poweroff,
    evaluate,
    run_ring_child,
)
import scripts.product_use_rerun_failed_legs as _rerun_mod  # noqa: E402

RING_TIMEOUT_S = int(os.environ.get("PRODUCT_USE_RING_TIMEOUT_S", "600"))
_rerun_mod.RING_TIMEOUT_S = RING_TIMEOUT_S


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


def main() -> int:
    started = _utc()
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_LAB_OVERLAY_PERSONA"] = "rc002"
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

    work = ROOT / "artifacts/product_use/interactive_guest_session_resume_open"
    session, attach = attach_session(work)
    _log(f"attach {attach}")
    if session is None or not attach.get("ok"):
        (OUT / "RESUME_OPEN_SUMMARY.json").write_text(
            json.dumps({"error": "attach_failed", "attach": attach}, indent=2) + "\n"
        )
        return 1

    inventory = {
        "G11": _load(OUT / "G11_waike" / "result.json"),
        "G12": _load(OUT / "G12_office" / "result.json"),
        "DOCK": _load(OUT / "DOCK_CONTINUITY.json"),
        "G13": _load(OUT / "G13_teacher" / "result.json"),
        "G15": _load(OUT / "G15_creative" / "result.json"),
        "REBOOT": _load(OUT / "REBOOT_UPDATE_RECOVERY.json"),
    }
    results: dict[str, Any] = {
        "G15": inventory["G15"],
        "REBOOT": inventory["REBOOT"],
    }
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_002.resume_open_attach.v1",
        "started_at_utc": started,
        "attach": attach,
        "kept": {
            "G11_hid_quiz": inventory["G11"].get("hid_quiz_submit"),
            "G11_offline": (inventory["G11"].get("offline") or {}).get("ok"),
            "G12": inventory["G12"].get("ok"),
            "DOCK": inventory["DOCK"].get("ok"),
            "G13": inventory["G13"].get("ok"),
            "G15": inventory["G15"].get("ok"),
            "REBOOT": inventory["REBOOT"].get("ok"),
        },
        "rerun": ["G14", "RING", "FOUR_GAME"],
        "ring_timeout_s": RING_TIMEOUT_S,
        "sealed_cow_only": True,
        "second_qemu": False,
    }

    try:
        _log("G14")
        g14_dir = OUT / "G14_dsxl_s1"
        g14_dir.mkdir(parents=True, exist_ok=True)
        results["G14"] = run_g14(session, g14_dir)
        results["G14"]["dsxl"] = attempt_dsxl_dual_compositor_pass(session, g14_dir)
        (g14_dir / "result.json").write_text(
            json.dumps(results["G14"], indent=2, default=str) + "\n"
        )
        _log(
            f"G14 ok={results['G14'].get('ok')} "
            f"git={((results['G14'].get('git_build_test') or {}).get('ok'))} "
            f"dsxl={((results['G14'].get('dsxl') or {}).get('DSXL_DUAL_COMPOSITOR_UX_PASS'))}"
        )

        _log(f"RING timeout_s={RING_TIMEOUT_S}")
        results["RING"] = run_ring_child(work)
        _log(
            f"RING pass={results['RING'].get('RING_TO_REAL_APP_STATE_MUTATION_PASS')} "
            f"blocker={results['RING'].get('blocker')}"
        )

        merge = {
            "G11": inventory["G11"],
            "G12": inventory["G12"],
            "G13": inventory["G13"],
            "G14": results["G14"],
            "G15": inventory["G15"],
            "RING": results["RING"],
            "DOCK": inventory["DOCK"],
        }
        update_persona_table(merge)

        power = clean_poweroff(session, work)
        summary["poweroff"] = power
        _log(f"poweroff {power}")

        staging = prepare_owner_guest_staging(ROOT)
        _log(f"staging_ok={staging.get('ok')}")
        if power.get("exited") and staging.get("ok"):
            assert_no_qemu()
            _log("FOUR_GAME")
            os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging.get("staging"))
            four_work = ROOT / "artifacts/wp011r/interactive_guest_session_four"
            four_work.mkdir(parents=True, exist_ok=True)
            tmpl = Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd")
            if tmpl.is_file():
                shutil.copyfile(tmpl, four_work / "edk2-aarch64-vars.fd")
            for name in ("qemu.pid", "qemu_boot.log"):
                p = four_work / name
                if p.exists() or p.is_symlink():
                    try:
                        p.unlink()
                    except OSError:
                        pass
            boot2 = boot_interactive_guest(
                ROOT, four_work, dual=True, boot_timeout_s=300, memory_mb=3072
            )
            sess2 = boot2.pop("_session", None)
            if not boot2.get("ok") or sess2 is None:
                results["FOUR_GAME"] = {
                    "ok": False,
                    "boot": boot2,
                    "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
                }
            else:
                try:
                    for _ in range(40):
                        if _agent_call(sess2, "compositor_info", timeout_sec=10.0).get("available"):
                            break
                        time.sleep(2)
                    evid = _evidence_dir(ROOT, "games")
                    results["FOUR_GAME"] = attempt_owner_four_game_in_guest_pass(
                        sess2, ROOT, evid
                    )
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
                        "git_ok": ((v or {}).get("git_build_test") or {}).get("ok"),
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
        (OUT / "RESUME_OPEN_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
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
        # honesty sync gaps
        try:
            gaps_path = ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json"
            gaps = json.loads(gaps_path.read_text())
            pt = gaps.setdefault("pass_tokens", {})
            four = results.get("FOUR_GAME") or {}
            ring = results.get("RING") or {}
            pt["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] = bool(
                four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
            )
            pt["RING_TO_REAL_APP_STATE_MUTATION_PASS"] = bool(
                ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
            )
            pt["RING_TO_REAL_APPLICATION_INPUT_PASS"] = bool(
                ring.get("RING_TO_REAL_APPLICATION_INPUT_PASS")
            )
            pt["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] = False
            gaps["five_gate_digital_and"] = all(
                [
                    pt.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"),
                    pt.get("LIVE_GUNNCHOS_VISUAL_PASS"),
                    pt.get("DSXL_DUAL_COMPOSITOR_UX_PASS"),
                    pt.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"),
                    pt.get("ECO010_SOAK_PASS"),
                ]
            )
            gaps["updated_at_utc"] = _utc()
            gaps_path.write_text(json.dumps(gaps, indent=2) + "\n")
            score_path = ROOT / "artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json"
            score = json.loads(score_path.read_text())
            obs = score.setdefault("tokens_observed", {})
            for k in (
                "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
                "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            ):
                obs[k] = pt.get(k)
            obs["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] = False
            score["five_gate_digital_and"] = gaps["five_gate_digital_and"]
            score_path.write_text(json.dumps(score, indent=2) + "\n")
        except Exception as exc:  # noqa: BLE001
            summary["gaps_sync_error"] = str(exc)

        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 0
    except Exception as exc:  # noqa: BLE001
        import traceback

        summary["error"] = str(exc)
        summary["traceback"] = traceback.format_exc()
        summary["partial"] = {k: (v or {}).get("ok") for k, v in results.items()}
        summary["finished_at_utc"] = _utc()
        (OUT / "RESUME_OPEN_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
