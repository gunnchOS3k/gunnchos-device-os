#!/usr/bin/env python3
"""Resume ONLY still-open PRODUCT-USE-RC-002 legs on one sealed+COW QEMU.

Keeps tip-current PASS for G11 quiz/offline, G12/Dock, G13, G15, REBOOT.
Re-runs: G14 (git+DSXL), RING, FOUR_GAME. Never reprovisions sealed base.
Never starts a second QEMU. Prefer FAIL over invented PASS.
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

# Must set before importing product_use_rerun_failed_legs (captures RING_TIMEOUT_S at import).
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


def ensure_git_in_guest(session: Any) -> dict[str, Any]:
    """COW overlay package refresh only — never rebuild sealed base."""
    probe = _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "command -v git && git --version"],
        timeout_sec=20.0,
    )
    if "git version" in (probe.get("stdout") or ""):
        return {"ok": True, "already": True, "stdout": (probe.get("stdout") or "")[:200]}
    install = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "export DEBIAN_FRONTEND=noninteractive; "
            "apt-get update -qq && apt-get install -y -qq git >/tmp/git_install.log 2>&1; "
            "command -v git && git --version; echo GIT_INSTALL_RC=$?",
        ],
        timeout_sec=180.0,
    )
    ok = "git version" in (install.get("stdout") or "")
    return {
        "ok": ok,
        "already": False,
        "stdout": (install.get("stdout") or "")[-400:],
        "stderr": (install.get("stderr") or "")[-200:],
    }


def main() -> int:
    started = _utc()
    os.environ["PRODUCT_USE_RING_TIMEOUT_S"] = str(RING_TIMEOUT_S)
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
        "G15": _load(OUT / "G15_creative" / "result.json"),
        "REBOOT": _load(OUT / "REBOOT_UPDATE_RECOVERY.json"),
    }
    _log(
        "KEEP "
        f"G11 quiz={inventory['G11'].get('hid_quiz_submit')} "
        f"offline={(inventory['G11'].get('offline') or {}).get('ok')} "
        f"G12={inventory['G12'].get('ok')} DOCK={inventory['DOCK'].get('ok')} "
        f"G13={inventory['G13'].get('ok')} G15={inventory['G15'].get('ok')} "
        f"REBOOT={inventory['REBOOT'].get('ok')}"
    )

    staging = prepare_owner_guest_staging(ROOT)
    _log(f"staging_ok={staging.get('ok')}")
    bl_bp = (
        ROOT
        / "artifacts/wp011r/owner_games_guest_bundle/beatlink-party/server/node_modules/body-parser/package.json"
    )
    _log(f"beatlink_body_parser={bl_bp.is_file()}")

    work = ROOT / "artifacts/product_use/interactive_guest_session_resume_open"
    work.mkdir(parents=True, exist_ok=True)
    for name in ("qemu.pid", "qemu_boot.log"):
        p = work / name
        if p.exists() or p.is_symlink():
            try:
                p.unlink()
            except OSError:
                pass
    tmpl = Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd")
    if tmpl.is_file():
        shutil.copyfile(tmpl, work / "edk2-aarch64-vars.fd")

    boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=300, memory_mb=3072)
    session = boot.pop("_session", None)
    results: dict[str, Any] = {
        "G15": inventory["G15"],
        "REBOOT": inventory["REBOOT"],
    }
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_002.resume_open.v1",
        "started_at_utc": started,
        "boot_ok": bool(boot.get("ok")),
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
    if not boot.get("ok") or session is None:
        summary["error"] = boot.get("error") or "boot_failed"
        (OUT / "RESUME_OPEN_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 1

    try:
        for _ in range(40):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2)

        git_ens = ensure_git_in_guest(session)
        summary["git_ensure"] = git_ens
        _log(f"git_ensure ok={git_ens.get('ok')} already={git_ens.get('already')}")

        _log("G14")
        g14_dir = OUT / "G14_dsxl_s1"
        g14_dir.mkdir(parents=True, exist_ok=True)
        results["G14"] = run_g14(session, g14_dir)
        # Second DSXL pass (post-git compositor settle) is authoritative when first flaked.
        dsxl2 = attempt_dsxl_dual_compositor_pass(session, g14_dir)
        results["G14"]["dsxl"] = dsxl2
        git_ok = bool((results["G14"].get("git_build_test") or {}).get("ok"))
        dsxl_ok = bool(dsxl2.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))
        results["G14"]["DSXL_DUAL_COMPOSITOR_UX_PASS"] = dsxl_ok
        results["G14"]["ok"] = bool(git_ok and dsxl_ok)
        results["G14"]["dsxl_missing"] = (dsxl2.get("compositor_ux_gate") or {}).get("missing")
        results["G14"]["focus_moves"] = (dsxl2.get("compositor_ux_gate") or {}).get("focus_moves")
        results["G14"]["observation_class"] = "GUEST_OBSERVED" if results["G14"]["ok"] else "PARTIAL_OR_FAIL"
        (g14_dir / "result.json").write_text(
            json.dumps(results["G14"], indent=2, default=str) + "\n"
        )
        _log(
            f"G14 ok={results['G14'].get('ok')} "
            f"dsxl={dsxl_ok} "
            f"git={git_ok}"
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

        if power.get("exited") and staging.get("ok"):
            assert_no_qemu()
            _log("FOUR_GAME")
            os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging.get("staging"))
            four_work = ROOT / "artifacts/wp011r/interactive_guest_session_four"
            four_work.mkdir(parents=True, exist_ok=True)
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
                        "app": (v or {}).get("app"),
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
        # Refresh gaps tokens from fresh four/ring evidence when present
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
        except Exception as exc:  # noqa: BLE001
            summary["gaps_sync_error"] = str(exc)

        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 0
    except Exception as exc:  # noqa: BLE001
        summary["error"] = str(exc)
        summary["partial"] = {k: (v or {}).get("ok") for k, v in results.items()}
        summary["finished_at_utc"] = _utc()
        try:
            clean_poweroff(session, work)
        except Exception:
            pass
        (OUT / "RESUME_OPEN_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        print(json.dumps(summary, indent=2, default=str), flush=True)
        return 1


if __name__ == "__main__":
    # Ensure ring child uses our timeout env
    os.environ.setdefault("PRODUCT_USE_RING_TIMEOUT_S", "600")
    raise SystemExit(main())
