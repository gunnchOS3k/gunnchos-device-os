#!/usr/bin/env python3
"""PRODUCT-USE finite subset: honest Ring re-earn + G11 in-guest WAIKE (+ optional G13/G15).

Does not flip persona tokens. Does not merge. Prefer FAIL over false PASS.
"""
from __future__ import annotations

import argparse
import base64
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

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    attempt_ring_app_mutation_pass,
    boot_interactive_guest,
)
from gunnchos_device_os.product_use.waike_guest_pack import write_guest_pack  # noqa: E402
from scripts.product_use_close_s1 import (  # noqa: E402
    _deploy_waike_server,
    run_g11,
    run_g13,
    run_g15,
    update_persona_table,
)

OUT = ROOT / "artifacts" / "product_use" / "journeys"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-g13", action="store_true")
    ap.add_argument("--with-g15", action="store_true")
    ap.add_argument("--skip-ring", action="store_true")
    ns = ap.parse_args(argv)

    started = _utc()
    OUT.mkdir(parents=True, exist_ok=True)
    pack_dir = ROOT / "artifacts/product_use/waike_guest_pack"
    pack = write_guest_pack(ROOT, pack_dir, course_id="GENERAL_IT")
    (OUT / "waike_guest_pack_build.json").write_text(json.dumps(pack, indent=2) + "\n")

    work = ROOT / "artifacts/product_use/interactive_guest_session_s1"
    work.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    boot = boot_interactive_guest(
        ROOT,
        work,
        dual=False,
        boot_timeout_s=int(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "300")),
        memory_mb=int(os.environ.get("GUNNCHDEVICE_LAB_MEMORY_MB", "4096")),
    )
    session = boot.pop("_session", None)
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_001.ring_g11_packet.v1",
        "started_at_utc": started,
        "boot_ok": bool(boot.get("ok")),
        "pack": pack,
        "prefer_fail_over_false_pass": True,
        "tokens_remain_false": True,
        "Edmund_mergeable": False,
        "LIVE_visual_retained": True,
    }
    if not boot.get("ok") or session is None:
        summary["error"] = boot.get("error") or "boot_failed"
        (OUT / "RING_G11_PACKET_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str))
        return 1

    results: dict[str, Any] = {}
    try:
        for _ in range(20):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2.0)

        if not ns.skip_ring:
            ring_dir = OUT / "G11_ring"
            ring_dir.mkdir(parents=True, exist_ok=True)
            ring_ev = _evidence_dir(ROOT, "ring")
            results["RING"] = attempt_ring_app_mutation_pass(session, ring_ev)
            src = ring_ev / "RING_APP_MUTATION_EVIDENCE.json"
            if src.exists():
                shutil.copy2(src, ring_dir / "RING_APP_MUTATION_EVIDENCE.json")
            for sub in ("document", "browser", "game"):
                sdir = ring_ev / sub
                ddir = ring_dir / sub
                if ddir.exists():
                    shutil.rmtree(ddir)
                if sdir.exists():
                    shutil.copytree(sdir, ddir)
            (ring_dir / "HONEST_REEARN_NOTE.json").write_text(
                json.dumps(
                    {
                        "lab_browser_collector_forbidden": True,
                        "pedestrian_seed_save_version": "2",
                        "migration_alone_forbidden": True,
                        "browser_surface": "RingMemo.html contenteditable → RingMemo.txt",
                        "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
                            results["RING"].get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
                        ),
                        "RING_TO_REAL_APPLICATION_INPUT_PASS": bool(
                            results["RING"].get("RING_TO_REAL_APPLICATION_INPUT_PASS")
                        ),
                        "RING_SPATIAL_ACCURACY": results["RING"].get("RING_SPATIAL_ACCURACY"),
                        "blocker": results["RING"].get("blocker"),
                    },
                    indent=2,
                )
                + "\n"
            )

        deploy = _deploy_waike_server(session, pack_dir)
        summary["deploy"] = {
            "curl": deploy.get("curl"),
            "start_ok": bool((deploy.get("start") or {}).get("ok")),
        }
        results["G11"] = run_g11(session)
        (OUT / "G11_waike").mkdir(parents=True, exist_ok=True)
        (OUT / "G11_waike" / "result.json").write_text(json.dumps(results["G11"], indent=2, default=str) + "\n")
        shutil.copytree(pack_dir, OUT / "G11_waike" / "pack", dirs_exist_ok=True)

        if ns.with_g13:
            results["G13"] = run_g13(session)
            (OUT / "G13_teacher").mkdir(parents=True, exist_ok=True)
            (OUT / "G13_teacher" / "result.json").write_text(
                json.dumps(results["G13"], indent=2, default=str) + "\n"
            )
        if ns.with_g15:
            results["G15"] = run_g15(session)
            (OUT / "G15_creative").mkdir(parents=True, exist_ok=True)
            (OUT / "G15_creative" / "result.json").write_text(
                json.dumps(results["G15"], indent=2, default=str) + "\n"
            )
            png_pull = _agent_call(
                session,
                "process_run",
                argv=[
                    "bash",
                    "-lc",
                    "python3 - <<'PY'\n"
                    "import base64,pathlib\n"
                    "p=pathlib.Path('/var/lib/gunnchos/creative/concept.png')\n"
                    "print(base64.b64encode(p.read_bytes()).decode() if p.exists() else '')\n"
                    "PY",
                ],
                timeout_sec=30.0,
            )
            b64 = (png_pull.get("stdout") or "").strip()
            if b64:
                (OUT / "G15_creative" / "concept.png").write_bytes(base64.b64decode(b64))

        table = update_persona_table(results)
        remaining = []
        ring = results.get("RING") or {}
        if not ns.skip_ring and not ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"):
            remaining.append(
                "RING_TO_REAL_APP_STATE_MUTATION_PASS still open after honest re-earn attempt"
            )
        if not results["G11"].get("ok"):
            remaining.append("G11 in-guest WAIKE lesson/quiz/offline incomplete")
        if ns.with_g13 and not (results.get("G13") or {}).get("ok"):
            remaining.append("G13 teacher assign/grade incomplete")
        if ns.with_g15 and not (results.get("G15") or {}).get("ok"):
            remaining.append("G15 creative export incomplete")
        remaining.extend(
            [
                "G14 DSXL focus_move / builder git (not in this packet unless separately run)",
                "Handheld dock continuity OPEN",
                "G11 reboot/resume schoolwork NOT_RUN",
                "Persona tokens remain false until full journeys",
            ]
        )
        summary.update(
            {
                "results": {
                    k: {kk: vv for kk, vv in v.items() if kk not in ("pull", "mutations")}
                    for k, v in results.items()
                },
                "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")),
                "RING_TO_REAL_APPLICATION_INPUT_PASS": bool(ring.get("RING_TO_REAL_APPLICATION_INPUT_PASS")),
                "RING_SPATIAL_ACCURACY": ring.get("RING_SPATIAL_ACCURACY") or "SIMULATED",
                "G11_ok": bool(results["G11"].get("ok")),
                "G13_ok": bool((results.get("G13") or {}).get("ok")) if ns.with_g13 else None,
                "G15_ok": bool((results.get("G15") or {}).get("ok")) if ns.with_g15 else None,
                "S1_remaining": remaining,
                "persona_table": "artifacts/product_use/PERSONA_JOURNEY_TABLE.json",
                "tokens_earned": {r["token_id"]: False for r in table.get("rows", [])},
                "finished_at_utc": _utc(),
            }
        )

        status_path = ROOT / "artifacts/product_use/PRODUCT_USE_RC_001_STATUS.json"
        status = json.loads(status_path.read_text()) if status_path.exists() else {}
        status["ring_g11_packet"] = {
            "started_at_utc": started,
            "finished_at_utc": summary["finished_at_utc"],
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": summary["RING_TO_REAL_APP_STATE_MUTATION_PASS"],
            "RING_TO_REAL_APPLICATION_INPUT_PASS": summary["RING_TO_REAL_APPLICATION_INPUT_PASS"],
            "RING_SPATIAL_ACCURACY": summary["RING_SPATIAL_ACCURACY"],
            "G11_ok": summary["G11_ok"],
            "G13_ok": summary["G13_ok"],
            "G15_ok": summary["G15_ok"],
            "Edmund_mergeable": False,
            "LIVE_visual_retained": True,
        }
        status["S1_open"] = remaining
        status["updated_at_utc"] = _utc()
        status["Edmund_mergeable"] = False
        status["persona_tokens"] = {
            "STUDENT_DIGITAL_PICKUP_AND_USE_READY": False,
            "OFFICE_DIGITAL_PICKUP_AND_USE_READY": False,
            "TEACHER_DIGITAL_PICKUP_AND_USE_READY": False,
            "BUILDER_DIGITAL_PICKUP_AND_USE_READY": False,
            "CREATIVE_DIGITAL_PICKUP_AND_USE_READY": False,
        }
        status_path.write_text(json.dumps(status, indent=2, default=str) + "\n")
    finally:
        try:
            session.stop()
        except Exception:  # noqa: BLE001
            pass

    (OUT / "RING_G11_PACKET_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
