#!/usr/bin/env python3
"""PRODUCT-USE-RC-002 orchestration — host preflight, pins, ingest, honesty, journeys.

Cursor never merges. Prefer FAIL over false PASS. Persona tokens true ONLY if
independently reproducible later. S1=0 for any token PASS.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.owner_four_game_artifacts import ACCEPTED_MAINS  # noqa: E402
from gunnchos_device_os.product_use.gunnchai_honesty import (  # noqa: E402
    consume_owner_matrix,
    write_consume_artifact,
)
from gunnchos_device_os.product_use.host_storage import preflight  # noqa: E402
from gunnchos_device_os.product_use.waike_guest_pack import write_guest_pack  # noqa: E402
from gunnchos_device_os.product_use.waike_owner_package import (  # noqa: E402
    REQUIRED_OWNER_COURSE_IDS,
    WaikeOwnerPackageStore,
)

OUT = ROOT / "artifacts" / "product_use"
PIN_REPOS = {
    "waike-research-ops": "waike-research-ops",
    "gunnchAI3k": "gunnchAI3k",
    "anime-aggressors": "anime-aggressors",
    "pedestrian-pursuit": "pedestrian-pursuit",
    "archive-of-life-artifact-world": "archive-of-life-artifact-world",
    "beatlink-party": "beatlink-party",
    "gunnchos-hardware-industrial-design": "gunnchos-hardware-industrial-design",
    "gunnchos-7gc-ai-ran-field-kit": "gunnchos-7gc-ai-ran-field-kit",
    "gunnchos-6g-security-trust-privacy-lab": "gunnchos-6g-security-trust-privacy-lab",
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def pin_owner_shas() -> dict[str, Any]:
    pins: dict[str, Any] = {}
    for key, sibling in PIN_REPOS.items():
        path = ROOT.parent / sibling
        if not path.is_dir():
            pins[key] = {"ok": False, "error": "missing", "path": str(path)}
            continue
        try:
            sha = _git(path, "rev-parse", "origin/main")
            subject = _git(path, "log", "-1", "--format=%s", sha)
            pins[key] = {
                "ok": True,
                "sha": sha,
                "short": sha[:12],
                "subject": subject,
                "path": str(path),
            }
        except subprocess.CalledProcessError as exc:
            pins[key] = {"ok": False, "error": str(exc), "path": str(path)}
    # Cross-check four-game ACCEPTED_MAINS table
    game_check = {}
    for game_id, meta in ACCEPTED_MAINS.items():
        sibling = meta["sibling"]
        live = (pins.get(sibling) or {}).get("sha")
        expected = meta["accepted_main_sha"]
        game_check[game_id] = {
            "expected": expected,
            "live_origin_main": live,
            "match": live == expected,
        }
    return {"pins": pins, "four_game_sha_check": game_check}


def ingest_waike() -> dict[str, Any]:
    owner = ROOT.parent / "waike-research-ops"
    store = WaikeOwnerPackageStore(ROOT)
    # Capture prior active for rollback proof
    prior = store._load_index().get("active_version")
    result = store.import_owner(owner, owner_commit=_git(owner, "rev-parse", "HEAD"))
    learner = store.view("learner")
    teacher = store.view("teacher")
    # Upgrade/rollback: activate prior (if any) then restore six-course active
    rollback_ok = False
    if prior and prior != result.get("package_version"):
        rb = store.rollback(prior)
        rollback_ok = bool(rb.get("ok"))
        store.activate(result["package_version"])
    pack = write_guest_pack(ROOT, OUT / "waike_guest_pack", course_id="GENERAL_IT")
    return {
        "ok": bool(result.get("ok")),
        "import": result,
        "learner_view_ok": bool(learner.get("ok")),
        "teacher_view_ok": bool(teacher.get("ok")),
        "learner_key_leak": "answer_keys" in json.dumps(learner.get("doc") or {}),
        "teacher_has_answer_keys": "answer_keys" in json.dumps(teacher.get("doc") or {}),
        "course_ids": result.get("course_ids"),
        "required_course_ids": sorted(REQUIRED_OWNER_COURSE_IDS),
        "twelve_course_ok": set(result.get("course_ids") or []) == REQUIRED_OWNER_COURSE_IDS,
        "nine_course_ok": False,  # superseded by twelve-course #46 catalog
        "six_course_ok": False,
        "stale_nine_course_active": False,
        "stale_six_course_active": False,
        "stale_three_course_active": False,
        "prior_version_retained_for_rollback": prior,
        "rollback_tested": rollback_ok if prior else False,
        "guest_pack": pack,
        "signing_tier": "DEV_TEST",
        "reauthored_in_device_os": False,
    }


def run_four_game_regression() -> dict[str, Any]:
    """Launch owner four-game guest regression if space allows."""
    env = os.environ.copy()
    env["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    cmd = [sys.executable, str(ROOT / "scripts" / "run_wp011r2_four_game_owner_reearn.py")]
    started = _utc()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=int(os.environ.get("PRODUCT_USE_FOUR_GAME_TIMEOUT", "2400")),
        )
        out_path = ROOT / "artifacts/wp011r/games/four_games_in_guest.json"
        payload = json.loads(out_path.read_text()) if out_path.exists() else {}
        return {
            "ok": proc.returncode == 0 and bool(payload.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")),
            "returncode": proc.returncode,
            "started_at_utc": started,
            "finished_at_utc": _utc(),
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
            "evidence": str(out_path.relative_to(ROOT)) if out_path.exists() else None,
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": bool(
                payload.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
            ),
            "surrogates": False,
            "ALPHA_reclassified_as_RC": False,
            "note": "Accepted-main regression only; do not reclassify ALPHA as RC.",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": "timeout",
            "started_at_utc": started,
            "finished_at_utc": _utc(),
            "stdout_tail": ((exc.stdout or b"") if isinstance(exc.stdout, (bytes, bytearray)) else (exc.stdout or ""))[
                -2000:
            ],
        }


def run_persona_closer(only: str | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    env["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    if only:
        env["PRODUCT_USE_S1_ONLY"] = only
    cmd = [sys.executable, str(ROOT / "scripts" / "product_use_close_s1.py")]
    started = _utc()
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("PRODUCT_USE_CLOSER_TIMEOUT", "3600")),
    )
    summary_path = OUT / "journeys" / "S1_CLOSER_SUMMARY.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "started_at_utc": started,
        "finished_at_utc": _utc(),
        "stdout_tail": (proc.stdout or "")[-3000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "summary": summary,
    }


def write_status(doc: dict[str, Any]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "PRODUCT_USE_RC_002_STATUS.json"
    path.write_text(json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def main() -> int:
    started = _utc()
    tip = _git(ROOT, "rev-parse", "HEAD")
    space = preflight(ROOT, cleanup_if_tight=True)
    (OUT / "HOST_STORAGE_PREFLIGHT.json").write_text(json.dumps(space, indent=2) + "\n")
    if space.get("HOST_RESOURCE_BLOCKED"):
        status = {
            "schema": "gunnchos.product_use_rc_002.status.v1",
            "work_item": "PRODUCT-USE-RC-002",
            "tip": tip,
            "started_at_utc": started,
            "finished_at_utc": _utc(),
            "HOST_RESOURCE_BLOCKED": True,
            "host_storage": space,
            "persona_tokens": {
                "STUDENT_DIGITAL_PICKUP_AND_USE_READY": False,
                "OFFICE_DIGITAL_PICKUP_AND_USE_READY": False,
                "TEACHER_DIGITAL_PICKUP_AND_USE_READY": False,
                "BUILDER_DIGITAL_PICKUP_AND_USE_READY": False,
                "CREATIVE_DIGITAL_PICKUP_AND_USE_READY": False,
            },
            "claim_boundary": "Blocked before QEMU — no invented guest PASS. Cursor does not merge.",
        }
        write_status(status)
        print(json.dumps(status, indent=2))
        return 2

    pins = pin_owner_shas()
    (OUT / "OWNER_SHA_PINS.json").write_text(json.dumps(pins, indent=2) + "\n")

    waike = ingest_waike()
    (OUT / "WAIKE_SIX_COURSE_INGEST.json").write_text(json.dumps(waike, indent=2) + "\n")

    ai = consume_owner_matrix(ROOT)
    write_consume_artifact(ROOT, ai)

    skip_guest = os.environ.get("PRODUCT_USE_RC_002_SKIP_GUEST", "").strip() in {"1", "true", "yes"}
    four: dict[str, Any]
    closer: dict[str, Any]
    if skip_guest:
        four = {"ok": False, "skipped": True, "reason": "PRODUCT_USE_RC_002_SKIP_GUEST"}
        closer = {"ok": False, "skipped": True, "reason": "PRODUCT_USE_RC_002_SKIP_GUEST"}
    else:
        # Mid-run space check before QEMU
        mid = preflight(ROOT, cleanup_if_tight=False)
        if mid.get("HOST_RESOURCE_BLOCKED"):
            four = {"ok": False, "HOST_RESOURCE_BLOCKED": True}
            closer = {"ok": False, "HOST_RESOURCE_BLOCKED": True}
        else:
            four = run_four_game_regression()
            (OUT / "FOUR_GAME_REGRESSION.json").write_text(json.dumps(four, indent=2, default=str) + "\n")
            mid2 = preflight(ROOT, cleanup_if_tight=True)
            if mid2.get("HOST_RESOURCE_BLOCKED"):
                closer = {"ok": False, "HOST_RESOURCE_BLOCKED": True, "host_storage": mid2}
            else:
                closer = run_persona_closer(os.environ.get("PRODUCT_USE_S1_ONLY"))
                (OUT / "PERSONA_CLOSER_RC002.json").write_text(
                    json.dumps(closer, indent=2, default=str) + "\n"
                )

    # Honest tokens: remain false unless persona table says otherwise after closer
    tokens = {
        "STUDENT_DIGITAL_PICKUP_AND_USE_READY": False,
        "OFFICE_DIGITAL_PICKUP_AND_USE_READY": False,
        "TEACHER_DIGITAL_PICKUP_AND_USE_READY": False,
        "BUILDER_DIGITAL_PICKUP_AND_USE_READY": False,
        "CREATIVE_DIGITAL_PICKUP_AND_USE_READY": False,
    }
    table_path = OUT / "PERSONA_JOURNEY_TABLE.json"
    table = json.loads(table_path.read_text()) if table_path.exists() else {"rows": []}
    for row in table.get("rows") or []:
        tid = row.get("token_id")
        if tid in tokens and row.get("token_earned") is True and int(row.get("S1") or 1) == 0:
            tokens[tid] = True

    s1_open: list[str] = []
    s2_open: list[str] = [
        "REAL_TEACHER_E6=false",
        "HUMAN_E6",
        "No GAME-RC-003 / AI-003 in this stream",
    ]
    if not (four.get("ok") or four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")):
        s1_open.append("FOUR_GAME accepted-main regression not PASS")
    if not waike.get("nine_course_ok"):
        s1_open.append("WAIKE nine-course ingest incomplete")
    if not ai.get("matrix_matches_9_1_6"):
        s1_open.append("gunnchAI honesty matrix not 9/1/6 (#35)")
    for row in table.get("rows") or []:
        if int(row.get("S1") or 0) > 0:
            s1_open.append(f"{row.get('persona')} S1 open: {row.get('primary_task') or row.get('WAIKE')}")

    status = {
        "schema": "gunnchos.product_use_rc_002.status.v1",
        "work_item": "PRODUCT-USE-RC-002",
        "stream": "A",
        "tip": tip,
        "started_at_utc": started,
        "finished_at_utc": _utc(),
        "HOST_RESOURCE_BLOCKED": False,
        "host_storage": space,
        "owner_sha_pins": pins,
        "waike_ingest": waike,
        "gunnchai_honesty": {
            "ok": ai.get("ok"),
            "counts": ai.get("counts"),
            "complete_ids": ai.get("complete_ids"),
            "partial_ids": ai.get("partial_ids"),
            "open_ids": ai.get("open_ids"),
            "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
            "persona_safe_capabilities": ai.get("persona_safe_capabilities"),
            "artifact": "artifacts/product_use/GUNNCHAI_HONESTY_CONSUMED.json",
        },
        "four_game_regression": four,
        "FOUR_GAME_ACCEPTED_MAIN_RC": bool(
            four.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
            and all((pins.get("four_game_sha_check") or {}).get(g, {}).get("match") for g in ACCEPTED_MAINS)
        ),
        "persona_closer": {
            "ok": closer.get("ok"),
            "returncode": closer.get("returncode"),
            "HOST_RESOURCE_BLOCKED": closer.get("HOST_RESOURCE_BLOCKED", False),
            "skipped": closer.get("skipped", False),
        },
        "persona_tokens": tokens,
        "S0_open": 0,
        "S1_open": s1_open,
        "S2_open": s2_open,
        "READY_FOR_EDMUND_MERGE": False,
        "EDMUND_MERGEABLE_FOR_THIS_PACKET": "NO",
        "cursor_never_merges": True,
        "prefer_fail_over_false_pass": True,
        "claim_boundary": (
            "PRODUCT-USE-RC-002 bounded DRAFT. Nine-course WAIKE owner ingest (#45) + gunnchAI #35 "
            "honesty consume (9/1/6) + accepted-main four-game attempt + persona closer. "
            "Persona tokens false unless independently earned with S1=0. Cursor does not merge."
        ),
    }
    write_status(status)
    print(json.dumps({k: status[k] for k in (
        "tip", "HOST_RESOURCE_BLOCKED", "waike_ingest", "gunnchai_honesty",
        "FOUR_GAME_ACCEPTED_MAIN_RC", "persona_tokens", "S1_open", "S2_open",
    ) if k in status}, indent=2, default=str)[:4000])
    return 0 if waike.get("ok") and ai.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
