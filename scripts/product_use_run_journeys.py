#!/usr/bin/env python3
"""PRODUCT-USE-RC-001 — run finite real Interactive Guest journeys for G11–G15 legs.

Uses Device Lab Interactive Development Guest (not HTML surrogate). Maps LIVE /
DSXL / RING evidence into persona cells. Persona tokens stay false unless a
full independently reproducible pickup-and-use path is closed.

Cursor never merges.
"""
from __future__ import annotations

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
    attempt_dsxl_dual_compositor_pass,
    attempt_live_visual_pass,
    attempt_ring_app_mutation_pass,
    boot_interactive_guest,
)
from gunnchos_device_os.product_use.personas import PERSONAS  # noqa: E402
from gunnchos_device_os.product_use.waike_owner_package import WaikeOwnerPackageStore  # noqa: E402


OUT = ROOT / "artifacts" / "product_use" / "journeys"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _copy_tree(src: Path, dst: Path) -> str | None:
    """Copy evidence dirs, skipping broken socket symlinks from prior QEMU runs."""
    if not src.exists():
        return None
    if dst.exists():
        shutil.rmtree(dst)

    def _ignore(directory: str, names: list[str]) -> set[str]:
        skip: set[str] = set()
        base = Path(directory)
        for name in names:
            p = base / name
            if name.endswith(".sock") or name.endswith(".pid"):
                skip.add(name)
                continue
            if p.is_symlink() and not p.exists():
                skip.add(name)
        return skip

    shutil.copytree(src, dst, ignore=_ignore, symlinks=False)
    return str(dst.relative_to(ROOT))


def _waike_teacher_isolation() -> dict[str, Any]:
    store = WaikeOwnerPackageStore(ROOT)
    learner = store.view("learner")
    teacher = store.view("teacher")
    learner_blob = json.dumps(learner.get("doc") or {})
    teacher_blob = json.dumps(teacher.get("doc") or {})
    leak = any(
        k in learner_blob
        for k in ("answer_keys", "answer_index", "instructor_notes", "instructor_keys")
    )
    return {
        "ok": bool(learner.get("ok") and teacher.get("ok") and not leak),
        "observation_class": "HOST_OBSERVED",
        "package_version": learner.get("package_version") or teacher.get("package_version"),
        "learner_key_leak": leak,
        "teacher_has_answer_keys": "answer_keys" in teacher_blob,
        "course_ids": learner.get("course_ids") or [],
        "note": "Owner #43 ingest projection only — not an in-guest WAIKE UI journey.",
    }


def _empty_row(pid: str) -> dict[str, Any]:
    p = PERSONAS[pid]
    return {
        "persona": pid,
        "name": p["name"],
        "profile": p["profile_id"],
        "boot": "NOT_RUN",
        "launcher": "NOT_RUN",
        "apps": "NOT_RUN",
        "network": "NOT_RUN",
        "primary_task": "NOT_RUN",
        "artifact": "NOT_RUN",
        "save": "NOT_RUN",
        "reboot": "NOT_RUN",
        "resume": "NOT_RUN",
        "offline": "NOT_RUN",
        "reconnect": "NOT_RUN",
        "AI": "NOT_RUN",
        "WAIKE": "NOT_RUN" if p.get("waike_role") else "N/A",
        "dock": "NOT_RUN" if p.get("dock") else "N/A",
        "Ring": "NOT_RUN" if p.get("ring") else "N/A",
        "game": "NOT_RUN" if p.get("game_source") else "N/A",
        "developer_intervention": "UNKNOWN",
        "terminal": "FORBIDDEN" if not p["terminal_allowed"] else "ALLOWED_NOT_RUN",
        "S0": 0,
        "S1": 0,
        "S2": 0,
        "evidence": "NONE",
        "token_earned": False,
        "token_id": p["token"],
        "VISUAL_MODEL_REVIEW": "UNAVAILABLE",
        "REAL_TEACHER_E6": False if pid == "G13" else None,
    }


def main() -> int:
    started = _utc()
    OUT.mkdir(parents=True, exist_ok=True)
    work = ROOT / "artifacts" / "product_use" / "interactive_guest_session"
    if work.exists():
        # Keep EDK2 vars if present; wipe stale sockets.
        for name in ("guest-agent.sock", "qemu-monitor.sock"):
            p = work / name
            if p.exists() or p.is_symlink():
                p.unlink()

    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_001.journey_run.v1",
        "started_at_utc": started,
        "prefer_fail_over_false_pass": True,
        "persona_tokens_policy": "false_unless_full_independently_reproducible_path",
        "VISUAL_MODEL_REVIEW_default": "UNAVAILABLE",
        "beatlink_usage": "BRANCH_EVIDENCE_ONLY",
        "gunnchai_usage": "accepted_main_only",
        "waike_owner": "waike-research-ops#43",
    }

    # --- WAIKE isolation (G13 prerequisite; HOST) ---
    waike = _waike_teacher_isolation()
    (OUT / "waike_teacher_isolation.json").write_text(json.dumps(waike, indent=2) + "\n")
    summary["waike_teacher_isolation"] = waike

    # --- Interactive Guest: LIVE + DSXL + RING ---
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    boot = boot_interactive_guest(
        ROOT,
        work,
        dual=True,
        boot_timeout_s=int(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "240")),
        memory_mb=int(os.environ.get("GUNNCHDEVICE_LAB_MEMORY_MB", "4096")),
    )
    session = boot.pop("_session", None)
    summary["boot"] = {k: boot.get(k) for k in boot if not str(k).startswith("_")}
    (OUT / "boot.json").write_text(json.dumps(summary["boot"], indent=2, default=str) + "\n")

    live: dict[str, Any] = {"ok": False, "skipped": True}
    dsxl: dict[str, Any] = {"ok": False, "skipped": True}
    ring: dict[str, Any] = {"ok": False, "skipped": True}

    if not boot.get("ok") or session is None:
        summary["error"] = boot.get("error") or "interactive_guest_boot_failed"
        summary["finished_at_utc"] = _utc()
        (OUT / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        _write_persona_table(summary, live, dsxl, ring, waike)
        print(json.dumps(summary, indent=2, default=str))
        return 1

    try:
        for _ in range(20):
            probe = _agent_call(session, "compositor_info", timeout_sec=10.0)
            if probe.get("available"):
                break
            time.sleep(2.0)

        visual_dir = _evidence_dir(ROOT, "visual")
        dsxl_dir = _evidence_dir(ROOT, "dsxl")
        ring_dir = _evidence_dir(ROOT, "ring")

        live = attempt_live_visual_pass(session, visual_dir)
        dsxl = attempt_dsxl_dual_compositor_pass(session, dsxl_dir)
        ring = attempt_ring_app_mutation_pass(session, ring_dir)

        summary["live_visual"] = {
            "ok": bool(live.get("ok") or live.get("LIVE_GUNNCHOS_VISUAL_PASS")),
            "LIVE_GUNNCHOS_VISUAL_PASS": bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS")),
            "observation_class": "GUEST_OBSERVED" if live.get("ok") or live.get("LIVE_GUNNCHOS_VISUAL_PASS") else "FAIL",
            "evidence_copy": _copy_tree(visual_dir, OUT / "G12_G11_live_visual"),
            "keys": sorted([k for k in live.keys() if k.isupper() or k in ("ok", "error", "blocker")]),
        }
        summary["dsxl"] = {
            "ok": bool(dsxl.get("ok") or dsxl.get("DSXL_DUAL_COMPOSITOR_PASS")),
            "DSXL_DUAL_COMPOSITOR_PASS": bool(dsxl.get("DSXL_DUAL_COMPOSITOR_PASS")),
            "observation_class": "GUEST_OBSERVED" if dsxl.get("ok") or dsxl.get("DSXL_DUAL_COMPOSITOR_PASS") else "FAIL",
            "evidence_copy": _copy_tree(dsxl_dir, OUT / "G14_dsxl"),
        }
        summary["ring"] = {
            "ok": bool(ring.get("ok") or ring.get("RING_APP_MUTATION_PASS")),
            "RING_APP_MUTATION_PASS": bool(ring.get("RING_APP_MUTATION_PASS")),
            "observation_class": "GUEST_OBSERVED" if ring.get("ok") or ring.get("RING_APP_MUTATION_PASS") else "FAIL",
            "evidence_copy": _copy_tree(ring_dir, OUT / "G11_ring"),
            "mutations": {
                k: ring.get(k)
                for k in (
                    "document_mutated",
                    "browser_mutated",
                    "game_mutated",
                    "libreoffice",
                    "browser",
                    "game",
                )
                if k in ring
            },
        }
        # Persist raw result snippets for audit
        (OUT / "live_visual_result.json").write_text(json.dumps(live, indent=2, default=str) + "\n")
        (OUT / "dsxl_result.json").write_text(json.dumps(dsxl, indent=2, default=str) + "\n")
        (OUT / "ring_result.json").write_text(json.dumps(ring, indent=2, default=str) + "\n")
    finally:
        try:
            session.stop()
        except Exception:  # noqa: BLE001
            pass

    summary["finished_at_utc"] = _utc()
    table = _write_persona_table(summary, live, dsxl, ring, waike)
    summary["persona_table_path"] = "artifacts/product_use/PERSONA_JOURNEY_TABLE.json"
    summary["tokens_earned"] = {
        row["token_id"]: row["token_earned"] for row in table["rows"]
    }
    (OUT / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    # Exit 0 even on partial — honesty over false green; CI should not require all PASSes.
    return 0


def _write_persona_table(
    summary: dict[str, Any],
    live: dict[str, Any],
    dsxl: dict[str, Any],
    ring: dict[str, Any],
    waike: dict[str, Any],
) -> dict[str, Any]:
    live_ok = bool(live.get("ok") or live.get("LIVE_GUNNCHOS_VISUAL_PASS"))
    dsxl_ok = bool(dsxl.get("ok") or dsxl.get("DSXL_DUAL_COMPOSITOR_PASS"))
    ring_ok = bool(ring.get("ok") or ring.get("RING_APP_MUTATION_PASS"))
    boot_ok = bool((summary.get("boot") or {}).get("ok"))
    pixels = False
    for base in (OUT / "G12_G11_live_visual", OUT / "G14_dsxl", OUT / "G11_ring"):
        if base.exists() and any(base.rglob("*.png")):
            pixels = True
            break
    visual = "AVAILABLE_CAPTURES" if pixels else "UNAVAILABLE"

    rows = [_empty_row(pid) for pid in ("G11", "G12", "G13", "G14", "G15")]
    by_id = {r["persona"]: r for r in rows}

    # Shared boot cell if interactive guest came up
    if boot_ok:
        for pid in ("G11", "G12", "G13", "G14"):
            by_id[pid]["boot"] = "GUEST_OBSERVED:interactive_guest_boot"
            by_id[pid]["developer_intervention"] = "AUTOMATED_GUEST_AGENT"

    # G11 — Ring + live doc/save + game mutation when ring ok
    g11 = by_id["G11"]
    g11["VISUAL_MODEL_REVIEW"] = visual
    if live_ok:
        g11["apps"] = "GUEST_OBSERVED:mousepad_document"
        g11["primary_task"] = "GUEST_OBSERVED:document_edit"
        g11["artifact"] = "GUEST_OBSERVED:gunnchos-lab-document.txt"
        g11["save"] = "GUEST_OBSERVED:ctrl_s_file_persist"
        g11["evidence"] = "artifacts/product_use/journeys/G12_G11_live_visual"
    if ring_ok:
        g11["Ring"] = "GUEST_OBSERVED:ring_app_state_mutation"
        g11["apps"] = (
            (g11["apps"] + "+libreoffice+chromium+godot")
            if g11["apps"] != "NOT_RUN"
            else "GUEST_OBSERVED:libreoffice+chromium+godot"
        )
        g11["game"] = "GUEST_OBSERVED:pedestrian_save_mutation_BRANCH_OR_ACCEPTED_ARTIFACT"
        g11["artifact"] = "GUEST_OBSERVED:odt+browser_state+pp_progression"
        g11["save"] = "GUEST_OBSERVED:guest_file_persist"
        g11["evidence"] = "artifacts/product_use/journeys/G11_ring (+ live if present)"
    g11["AI"] = "NOT_RUN"
    g11["WAIKE"] = "HOST_OBSERVED:owner_ingest_only" if waike.get("ok") else "NOT_RUN"
    g11["network"] = "NOT_RUN"
    g11["offline"] = "NOT_RUN"
    g11["reconnect"] = "NOT_RUN"
    g11["reboot"] = "NOT_RUN"
    g11["resume"] = "NOT_RUN"
    g11["launcher"] = "NOT_RUN"
    g11["S1"] = 1 if not (live_ok and ring_ok) else 0
    g11["S2"] = 1  # incomplete pickup-and-use matrix
    g11["token_earned"] = False  # full student day not closed

    # G12 — office doc/browser/save from LIVE (+ RING libreoffice/browser)
    g12 = by_id["G12"]
    g12["VISUAL_MODEL_REVIEW"] = visual
    if live_ok or ring_ok:
        g12["apps"] = "GUEST_OBSERVED:document+browser"
        g12["primary_task"] = "GUEST_OBSERVED:edit_and_save_document"
        g12["artifact"] = "GUEST_OBSERVED:saved_document_and_or_odt"
        g12["save"] = "GUEST_OBSERVED:guest_filesystem_persist"
        g12["evidence"] = "artifacts/product_use/journeys/G12_G11_live_visual (+ ring if present)"
    g12["dock"] = "OPEN"
    g12["network"] = "NOT_RUN"
    g12["offline"] = "NOT_RUN"
    g12["reconnect"] = "NOT_RUN"
    g12["reboot"] = "NOT_RUN"
    g12["resume"] = "NOT_RUN"
    g12["AI"] = "NOT_RUN"
    g12["launcher"] = "NOT_RUN"
    g12["S1"] = 1 if not (live_ok or ring_ok) else 0
    g12["S2"] = 1
    g12["token_earned"] = False

    # G13 — teacher: boot + WAIKE key isolation; no REAL_TEACHER_E6
    g13 = by_id["G13"]
    g13["VISUAL_MODEL_REVIEW"] = visual
    g13["WAIKE"] = (
        "HOST_OBSERVED:teacher_view_keys_isolated_from_learner"
        if waike.get("ok")
        else "FAIL_OR_MISSING_INGEST"
    )
    g13["primary_task"] = "HOST_OBSERVED:teacher_ingest_view" if waike.get("ok") else "NOT_RUN"
    g13["artifact"] = "HOST_OBSERVED:waike_store_teacher_ingest" if waike.get("ok") else "NOT_RUN"
    if live_ok:
        g13["apps"] = "GUEST_OBSERVED:document_surface_shared_with_student_profile"
        g13["save"] = "GUEST_OBSERVED:document_save"
    g13["AI"] = "NOT_RUN"
    g13["REAL_TEACHER_E6"] = False
    g13["evidence"] = "artifacts/product_use/journeys/waike_teacher_isolation.json"
    g13["S1"] = 1  # no in-guest instructor UI / cohort grading
    g13["S2"] = 1
    g13["token_earned"] = False

    # G14 — dual display
    g14 = by_id["G14"]
    g14["VISUAL_MODEL_REVIEW"] = visual
    if dsxl_ok:
        g14["primary_task"] = "GUEST_OBSERVED:dual_compositor_both_displays_useful"
        g14["apps"] = "GUEST_OBSERVED:foot+mousepad_dual"
        g14["artifact"] = "GUEST_OBSERVED:dsxl_evidence_pack"
        g14["evidence"] = "artifacts/product_use/journeys/G14_dsxl"
        g14["terminal"] = "GUEST_OBSERVED:foot_terminal_allowed_builder"
    else:
        g14["terminal"] = "ALLOWED_NOT_RUN"
    g14["AI"] = "NOT_RUN"
    g14["launcher"] = "NOT_RUN"
    g14["network"] = "NOT_RUN"
    g14["save"] = "NOT_RUN"
    g14["reboot"] = "NOT_RUN"
    g14["resume"] = "NOT_RUN"
    g14["S1"] = 1 if not dsxl_ok else 0
    g14["S2"] = 1  # git/clone/build/sdk not closed
    g14["token_earned"] = False

    # G15 — creative remains OPEN / NOT_RUN (no mature in-guest creator)
    g15 = by_id["G15"]
    g15["VISUAL_MODEL_REVIEW"] = "UNAVAILABLE"
    g15["boot"] = "NOT_RUN"
    g15["dock"] = "OPEN"
    g15["S1"] = 1
    g15["S2"] = 1
    g15["token_earned"] = False
    g15["evidence"] = "NONE — mature in-guest creative app not closed; toy surface forbidden"

    # Handheld dock continuity global
    dock_continuity = "OPEN"

    table = {
        "schema": "gunnchos.product_use.persona_journey_table.v1",
        "generated_at_utc": _utc(),
        "note": (
            "Finite Interactive Guest subset only. Persona tokens remain false. "
            "VISUAL_MODEL_REVIEW is UNAVAILABLE unless PNG captures exist in evidence packs."
        ),
        "tokens_earned": False,
        "VISUAL_MODEL_REVIEW": visual,
        "handheld_dock_continuity": dock_continuity,
        "ring_mutation": "GUEST_OBSERVED" if ring_ok else "OPEN",
        "rows": rows,
        "run_summary": "artifacts/product_use/journeys/RUN_SUMMARY.json",
    }
    path = ROOT / "artifacts" / "product_use" / "PERSONA_JOURNEY_TABLE.json"
    path.write_text(json.dumps(table, indent=2) + "\n")
    return table


if __name__ == "__main__":
    raise SystemExit(main())
