#!/usr/bin/env python3
"""WP-011R.2: re-earn FOUR_GAME via owner artifacts inside Interactive Guest.

Cursor never merges. Prefer FAIL with exact blockers over false PASS.
Keeps LIVE/DSXL/RING/ECO010 evidence tokens unless this run regenerates them.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_four_game_guest import (  # noqa: E402
    LAB_IDS,
    attempt_owner_four_game_in_guest_pass,
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sync_tokens(four_pass: bool, four_result: dict) -> None:
    gaps_path = ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json"
    gaps = json.loads(gaps_path.read_text(encoding="utf-8"))
    gaps["pass_tokens"]["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] = bool(four_pass)
    gaps["updated_at_utc"] = _utc()
    gaps["assessed_tip"] = "wp011r2-owner-four-game"
    # Update FOUR_GAME gap entry
    for bucket in ("gaps", "remaining"):
        items = gaps.get(bucket) or []
        for g in items:
            if g.get("token") == "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS":
                g["earned"] = bool(four_pass)
                g["pass"] = bool(four_pass)
                g["digital_earned"] = bool(four_pass)
                g["status"] = "EARNED" if four_pass else "OPEN_WP011R2"
                g["summary"] = (
                    "EARNED: owner accepted-main artifacts in Interactive Guest "
                    "(Godot anime/pedestrian; Archive Chromium native save; Beat Link Socket.IO)"
                    if four_pass
                    else (
                        "OPEN: "
                        + json.dumps(four_result.get("blockers") or four_result.get("blocker"))
                    )
                )
                g["evidence"] = "artifacts/wp011r/games/four_games_in_guest.json"
    if four_pass:
        gaps["remaining"] = [
            r
            for r in (gaps.get("remaining") or [])
            if r.get("token") != "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"
        ]
        gaps.setdefault("closed_this_cycle", [])
        if "FOUR_GAME owner-artifact Interactive Guest PASS" not in gaps["closed_this_cycle"]:
            gaps["closed_this_cycle"].append("FOUR_GAME owner-artifact Interactive Guest PASS")
    # five-gate digital AND
    pt = gaps["pass_tokens"]
    five = all(
        bool(pt.get(t))
        for t in (
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "ECO010_SOAK_PASS",
        )
    )
    gaps["five_gate_digital_and"] = five
    gaps["master_complete"] = False  # shipping still false
    gaps["shipping_master"] = False
    gaps["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] = False
    gaps["claim_firewall"]["SHIPPING_IMAGE"] = False
    gaps["claim_firewall"]["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] = False
    gaps["independent"] = {
        "INDEPENDENT_PASS": five,
        "reason": (
            "five_gate_digital_and true after FOUR_GAME owner-artifact re-earn"
            if five
            else "five_gate_digital_and false until FOUR_GAME + retained gates"
        ),
    }
    gaps["INDEPENDENT_PASS"] = five
    gaps["note"] = (
        "WP-011R.2 owner-artifact FOUR_GAME attempt. Historical #103 not revived as final. "
        "SHIPPING_IMAGE=false; VF4-6 PHYSICAL_PENDING."
    )
    gaps_path.write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")

    tokens_path = ROOT / "gunnchos_device_os/device_lab/TOKENS_WP011.json"
    tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    tokens["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] = bool(four_pass)
    tokens["updated_at_utc"] = _utc()
    tokens_path.write_text(json.dumps(tokens, indent=2) + "\n", encoding="utf-8")

    recon_path = ROOT / "artifacts/wp011r/WP011R2_RECONCILIATION.json"
    recon = json.loads(recon_path.read_text(encoding="utf-8"))
    recon["gates"]["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] = "PASS" if four_pass else "FAIL"
    recon["at_utc"] = _utc()
    if four_pass:
        recon["remaining_blockers"] = [
            b
            for b in recon.get("remaining_blockers") or []
            if "FOUR_GAME" not in b
        ]
        recon["remaining_blockers"].append(
            "Independent re-verify five_gate_digital_and after FOUR_GAME"
        )
        recon["remaining_blockers"].append(
            "VF4-6 PHYSICAL_PENDING; SILICON_EXACT_EMULATION=false; SHIPPING_IMAGE=false"
        )
    else:
        recon["remaining_blockers"] = [
            f"FOUR_GAME blockers: {json.dumps(four_result.get('blockers') or four_result.get('blocker'))}",
            "VF4-6 PHYSICAL_PENDING; SILICON_EXACT_EMULATION=false; SHIPPING_IMAGE=false",
        ]
    recon_path.write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")

    # Register yaml token
    reg = ROOT / "gunnchos_device_os/device_lab/device_lab_v1/DEVICE_LAB_COMPLETION_REGISTER.yaml"
    text = reg.read_text(encoding="utf-8")
    text2 = text.replace(
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS: false",
        f"FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS: {'true' if four_pass else 'false'}",
    ).replace(
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS: true",
        f"FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS: {'true' if four_pass else 'false'}",
    )
    if text2 != text:
        reg.write_text(text2, encoding="utf-8")


def main() -> int:
    work = ROOT / "artifacts" / "wp011r" / "interactive_guest_session_four"
    work.mkdir(parents=True, exist_ok=True)
    edk2_vars_src = Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd")
    if edk2_vars_src.is_file():
        shutil.copyfile(edk2_vars_src, work / "edk2-aarch64-vars.fd")

    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    # Allow guest→host HTTP fallback; primary deploy uses virtio-9p.
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")
    from gunnchos_device_os.device_lab.owner_four_game_artifacts import (
        prepare_owner_guest_staging,
    )

    staging_meta = prepare_owner_guest_staging(ROOT)
    # Always expose staging even if Godot copy is provenance-locked; packages still refresh.
    os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(
        staging_meta.get("staging") or (ROOT / "artifacts/wp011r/owner_games_guest_bundle")
    )
    js = Path(os.environ["GUNNCH_LAB_GAMES_9P_PATH"]) / "lab_observe_only.js"
    print("staging_ok", staging_meta.get("ok"), "observe_start", "__aolStartExpedition" in js.read_text(encoding="utf-8", errors="ignore"), flush=True)
    boot = boot_interactive_guest(ROOT, work, dual=True, boot_timeout_s=300, memory_mb=4096)
    session = boot.pop("_session", None)
    out: dict = {"boot": {"ok": boot.get("ok"), "error": boot.get("error")}, "at_utc": _utc()}
    if not boot.get("ok") or session is None:
        (ROOT / "artifacts/wp011r/games/four_game_run_summary.json").write_text(
            json.dumps({"summary": out, "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False}, indent=2)
            + "\n"
        )
        print(json.dumps(out, indent=2))
        return 1
    try:
        for _ in range(40):
            c = _agent_call(session, "compositor_info")
            if c.get("available"):
                break
            time.sleep(2)
        evid = _evidence_dir(ROOT, "games")
        four = attempt_owner_four_game_in_guest_pass(session, ROOT, evid)
        out["four_game"] = {
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": four.get(
                "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"
            ),
            "blocker": four.get("blocker"),
            "blockers": four.get("blockers"),
            "games": {
                g: (four.get("games") or {}).get(g, {}).get("FOUR_GAME_REAL_RUNTIME_EARNED")
                for g in LAB_IDS
            },
        }
        _sync_tokens(bool(four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")), four)
        # Independent score recompute
        try:
            from scripts.device_lab_score_independent import main as score_main  # type: ignore

            score_main([])
        except Exception:
            # Fallback: invoke as module file
            import subprocess

            subprocess.run(
                [sys.executable, str(ROOT / "scripts/device_lab_score_independent.py")],
                cwd=str(ROOT),
                check=False,
            )
    finally:
        try:
            session.stop()
        except Exception:
            pass

    summary = {
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": out.get("four_game", {}).get(
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"
        ),
        "games": out.get("four_game", {}).get("games"),
        "blockers": out.get("four_game", {}).get("blockers") or out.get("four_game", {}).get("blocker"),
        "at_utc": _utc(),
    }
    (ROOT / "artifacts/wp011r/games/four_game_run_summary.json").write_text(
        json.dumps({"summary": summary, "detail": out}, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
