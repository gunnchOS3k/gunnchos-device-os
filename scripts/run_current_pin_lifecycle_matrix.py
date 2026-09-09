#!/usr/bin/env python3
"""Derive CURRENT_PIN_APP_LIFECYCLE_MATRIX from authentic evidence (fail-closed).

Never emits a fake PASS. Rows must be backed by pin-bound evidence artifacts
produced by real guest / product runners. Optional --execute probes a live
Interactive Guest session when available; absent authentic evidence → FAIL.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.current_pin_manifest import (  # noqa: E402
    LIFECYCLE_PRODUCTS,
    LIFECYCLE_STEPS,
    PinManifestError,
    load_pin_manifest,
    pin_sha_for,
)

OUT_DIR = ROOT / "artifacts" / "device_lab_current_pin"
MATRIX_PATH = OUT_DIR / "LIFECYCLE_MATRIX.json"
GATE_PATH = OUT_DIR / "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_error": "invalid_json", "path": str(path)}


def _evidence_candidates(product: str) -> list[Path]:
    """Known authentic evidence locations per product (current-pin or wp011r)."""
    base = ROOT / "artifacts"
    mapping: dict[str, list[Path]] = {
        "anime-aggressors": [
            base / "wp011r/games/four_games_in_guest.json",
            base / "device_lab_current_pin/FOUR_GAME_CURRENT_PIN.json",
        ],
        "pedestrian-pursuit": [
            base / "wp011r/games/four_games_in_guest.json",
            base / "device_lab_current_pin/FOUR_GAME_CURRENT_PIN.json",
        ],
        "archive-of-life-artifact-world": [
            base / "wp011r/games/four_games_in_guest.json",
            base / "device_lab_current_pin/FOUR_GAME_CURRENT_PIN.json",
        ],
        "beatlink-party": [
            base / "wp011r/games/four_games_in_guest.json",
            base / "device_lab_current_pin/FOUR_GAME_CURRENT_PIN.json",
        ],
        "gunnchos-waike-learning-platform": [
            base / "device_lab_current_pin/WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS.json",
            base / "product_use_rc_002/WAIKE_RUNTIME.json",
            base / "wp011r/waike/WAIKE_RUNTIME.json",
        ],
        "gunnchAI3k": [
            base / "device_lab_current_pin/GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS.json",
            base / "wp011r/gunnchai/GUNNCHAI_INTEGRATION.json",
        ],
        "gunnchos-device-os": [
            base / "device_lab_current_pin/LIVE_GUNNCHOS_VISUAL_PASS.json",
            base / "wp011r/visual/LIVE_VISUAL_EVIDENCE.json",
            base / "wp011r/ring/RING_APP_MUTATION_EVIDENCE.json",
        ],
    }
    return mapping.get(product, [])


def _step_from_evidence(product: str, step: str, blob: dict[str, Any], pin_sha: str) -> dict[str, Any]:
    """Map authentic evidence into a lifecycle step cell. Fail closed by default."""
    if not blob or blob.get("_error"):
        return {
            "product": product,
            "step": step,
            "ok": False,
            "reason": "evidence_missing_or_invalid",
            "pin_sha": pin_sha,
        }
    # Reject historical / withheld / host-stub packets for current-pin matrix.
    if blob.get("blocker") in {"HOST_RESOURCE_BLOCKED", "NOT_EXECUTED"}:
        return {
            "product": product,
            "step": step,
            "ok": False,
            "reason": f"evidence_withheld:{blob.get('blocker')}",
            "pin_sha": pin_sha,
        }
    if blob.get("DIGITAL_EMULATION_LABEL") == "NOT_EXECUTED":
        return {
            "product": product,
            "step": step,
            "ok": False,
            "reason": "not_executed",
            "pin_sha": pin_sha,
        }
    # Pin binding when present
    bound = blob.get("pin_manifest_sha256") or blob.get("accepted_main_sha") or blob.get("device_os_tip")
    games = blob.get("games") or blob.get("products") or {}
    product_blob = games.get(product) if isinstance(games, dict) else None

    authentic_markers = (
        blob.get("DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST") is True
        or blob.get("in_guest") is True
        or blob.get("guest_session_id")
        or blob.get("qemu_pid")
        or (isinstance(product_blob, dict) and product_blob.get("in_guest"))
        or blob.get("LIVE_GUNNCHOS_VISUAL_PASS") is True
        or blob.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS") is True
        or blob.get("RING_TO_REAL_APP_STATE_MUTATION_PASS") is True
        or blob.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS") is True
        or blob.get("GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS") is True
    )
    if not authentic_markers:
        return {
            "product": product,
            "step": step,
            "ok": False,
            "reason": "no_authentic_guest_or_runtime_marker",
            "pin_sha": pin_sha,
            "bound_field": bound,
        }

    lifecycle = blob.get("lifecycle") or blob.get("lifecycle_steps") or {}
    if isinstance(lifecycle, dict) and step in lifecycle:
        cell = lifecycle[step]
        ok = bool(cell.get("ok") if isinstance(cell, dict) else cell)
        return {
            "product": product,
            "step": step,
            "ok": ok,
            "reason": "lifecycle_field" if ok else "lifecycle_field_false",
            "pin_sha": pin_sha,
            "source": "embedded_lifecycle",
        }

    # Coarse mapping from known gate tokens — only for steps that those gates cover.
    coarse_ok = False
    reason = "step_not_covered_by_evidence"
    if step in {"clean_launch", "first_run"} and (
        blob.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        or blob.get("LIVE_GUNNCHOS_VISUAL_PASS")
        or blob.get("WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS")
        or blob.get("GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS")
    ):
        coarse_ok = True
        reason = "mapped_from_runtime_pass"
    elif step in {"save_persist", "restart", "restore"} and (
        blob.get("FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS")
        or blob.get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
    ):
        coarse_ok = True
        reason = "mapped_from_mutation_or_four_game"
    elif step == "crash_fatal_scan" and blob.get("crash_fatal_clean") is True:
        coarse_ok = True
        reason = "crash_fatal_clean"
    # Remaining steps require explicit lifecycle evidence — fail closed.
    return {
        "product": product,
        "step": step,
        "ok": coarse_ok,
        "reason": reason if coarse_ok else "explicit_lifecycle_evidence_required",
        "pin_sha": pin_sha,
        "source": "coarse_map" if coarse_ok else None,
    }


def derive_matrix(
    *,
    pin_doc: dict[str, Any],
    execute_guest: bool = False,
) -> dict[str, Any]:
    pin_hash = str(pin_doc.get("manifest_sha256"))
    device_os_tip = pin_sha_for(pin_doc, "gunnchos-device-os")
    rows: list[dict[str, Any]] = []
    for product in LIFECYCLE_PRODUCTS:
        try:
            product_pin = pin_sha_for(pin_doc, product)
        except PinManifestError as exc:
            for step in LIFECYCLE_STEPS:
                rows.append(
                    {
                        "product": product,
                        "step": step,
                        "ok": False,
                        "reason": str(exc),
                        "pin_sha": None,
                    }
                )
            continue
        evidence_blob: dict[str, Any] = {}
        evidence_path: str | None = None
        for cand in _evidence_candidates(product):
            blob = _load_json(cand)
            if blob and not blob.get("_error"):
                evidence_blob = blob
                evidence_path = str(cand)
                break
        for step in LIFECYCLE_STEPS:
            cell = _step_from_evidence(product, step, evidence_blob, product_pin)
            cell["evidence_path"] = evidence_path
            cell["pin_manifest_sha256"] = pin_hash
            rows.append(cell)

    guest_probe: dict[str, Any] | None = None
    if execute_guest:
        guest_probe = _try_guest_lifecycle_probe()
        if guest_probe and guest_probe.get("rows"):
            # Merge guest probe rows by (product, step) when they claim authentic ok.
            by_key = {(r["product"], r["step"]): i for i, r in enumerate(rows)}
            for gr in guest_probe["rows"]:
                key = (gr.get("product"), gr.get("step"))
                if key in by_key and gr.get("ok") is True and gr.get("authentic") is True:
                    rows[by_key[key]] = {
                        **rows[by_key[key]],
                        **gr,
                        "pin_manifest_sha256": pin_hash,
                    }

    all_ok = bool(rows) and all(bool(r.get("ok")) for r in rows)
    # Hard fail-closed: never PASS without execute when any step lacks authentic coverage
    if all_ok and not execute_guest:
        # Coarse-map alone is insufficient for matrix PASS — require explicit lifecycle
        # coverage for every step or guest execute. Prefer FAIL over false PASS.
        if any(r.get("source") == "coarse_map" for r in rows):
            all_ok = False
            blocker = "COARSE_MAP_INSUFFICIENT_WITHOUT_EXPLICIT_LIFECYCLE_OR_GUEST_EXECUTE"
        else:
            blocker = None
    else:
        blocker = None if all_ok else "LIFECYCLE_EVIDENCE_INCOMPLETE"

    matrix = {
        "schema": "gunnchos.device_lab.lifecycle_matrix.v1",
        "generated_at_utc": _utc(),
        "pin_manifest_sha256": pin_hash,
        "device_os_tip": device_os_tip,
        "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": all_ok,
        "blocker": blocker,
        "rows": rows,
        "products": list(LIFECYCLE_PRODUCTS),
        "required_steps": list(LIFECYCLE_STEPS),
        "execute_guest": bool(execute_guest),
        "guest_probe": guest_probe,
        "prefer_fail_over_false_pass": True,
        "note": (
            "Derived from pin-bound authentic evidence; coarse gate maps never alone "
            "earn matrix PASS without explicit lifecycle fields or guest execute."
        ),
    }
    return matrix


def _try_guest_lifecycle_probe() -> dict[str, Any]:
    """Best-effort Interactive Guest probe. Failures return authentic=false rows."""
    if os.environ.get("GUNNCH_GUEST_AGENT_HOST_STUB", "0") not in {"0", "", "false", "False"}:
        return {
            "ok": False,
            "error": "host_stub_forbidden_for_current_pin_lifecycle",
            "rows": [],
        }
    try:
        from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: WPS433
            _agent_call,
            boot_interactive_guest,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"import_failed:{exc}", "rows": []}

    session = None
    rows: list[dict[str, Any]] = []
    try:
        session = boot_interactive_guest(timeout_sec=180)
        # Minimal authenticity probe: guest agent reachable + weston/pids.
        ping = _agent_call(session, "ping", {}, timeout_sec=30)
        authentic = bool(ping.get("ok") or ping.get("pong") or ping.get("status") == "ok")
        for product in LIFECYCLE_PRODUCTS:
            for step in LIFECYCLE_STEPS:
                # Without product-specific lifecycle scripts, do not invent PASS.
                rows.append(
                    {
                        "product": product,
                        "step": step,
                        "ok": False,
                        "authentic": authentic,
                        "reason": "guest_reachable_but_product_lifecycle_not_instrumented"
                        if authentic
                        else "guest_probe_failed",
                        "guest_ping": ping,
                    }
                )
        return {"ok": authentic, "rows": rows, "ping": ping}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:500], "rows": rows}
    finally:
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass


def write_outputs(matrix: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    gate = {
        "schema": "gunnchos.device_lab.gate.CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS.v1",
        "generated_at_utc": matrix.get("generated_at_utc"),
        "pin_manifest_sha256": matrix.get("pin_manifest_sha256"),
        "device_os_tip": matrix.get("device_os_tip"),
        "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": bool(
            matrix.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS")
        ),
        "verdict": "PASS" if matrix.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS") else "FAIL",
        "blocker": matrix.get("blocker"),
        "reason": matrix.get("blocker")
        or (
            "all_lifecycle_rows_ok"
            if matrix.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS")
            else "lifecycle_rows_incomplete"
        ),
        "historical_tokens_not_reused": True,
        "DIGITAL_EMULATION_LABEL": "EXECUTED"
        if matrix.get("execute_guest")
        else "DERIVED_FAIL_CLOSED",
        "row_count": len(matrix.get("rows") or []),
        "rows_ok": sum(1 for r in (matrix.get("rows") or []) if r.get("ok")),
    }
    GATE_PATH.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Boot Interactive Guest and probe (still fail-closed without product lifecycle)",
    )
    args = parser.parse_args(argv)
    try:
        pin_doc = load_pin_manifest(ROOT)
    except PinManifestError as exc:
        matrix = {
            "schema": "gunnchos.device_lab.lifecycle_matrix.v1",
            "generated_at_utc": _utc(),
            "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": False,
            "blocker": str(exc),
            "rows": [],
            "products": list(LIFECYCLE_PRODUCTS),
            "required_steps": list(LIFECYCLE_STEPS),
            "prefer_fail_over_false_pass": True,
        }
        write_outputs(matrix)
        print(json.dumps(matrix, indent=2))
        return 1
    matrix = derive_matrix(pin_doc=pin_doc, execute_guest=bool(args.execute))
    write_outputs(matrix)
    print(json.dumps(matrix, indent=2))
    return 0 if matrix.get("CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
