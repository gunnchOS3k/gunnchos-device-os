"""Consume gunnchAI3k accepted-main honesty matrix + mastery (#37 tip).

Honesty matrix remains AI-USER-READY-003 (#35). Accepted tip is #37
(AI-WAIKE-MASTERY). Do NOT consume unmerged #36. Product UI and persona claims
MUST NOT label PARTIAL/OPEN tasks as COMPLETE.
Coverage truth: 9 COMPLETE / 1 PARTIAL / 6 OPEN (+ mastery eval sidecar).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "gunnchos.product_use.gunnchai_honesty_consume.v1"

# Authoritative post-#35 matrix (must match owner AI_USER_READY_003_RESULT coverage).
COMPLETE_IDS = (
    "AI-UR-001",
    "AI-UR-002",
    "AI-UR-003",
    "AI-UR-004",
    "AI-UR-005",
    "AI-UR-006",
    "AI-UR-007",
    "AI-UR-013",
    "AI-UR-016",
)
PARTIAL_IDS = (
    "AI-UR-011",  # vision/OCR — PARTIAL; not frontier VLM / COMPLETE product claim
)
OPEN_IDS = (
    "AI-UR-008",
    "AI-UR-009",
    "AI-UR-010",
    "AI-UR-012",
    "AI-UR-014",
    "AI-UR-015",
)

# Persona-facing capabilities that may be exercised (must be COMPLETE or honest PARTIAL).
PERSONA_SAFE_CAPABILITIES = {
    "local_fast": {"task_id": "AI-UR-016", "status": "COMPLETE"},
    "projects_memory": {"task_id": "AI-UR-002", "status": "COMPLETE"},
    "source_grounded": {"task_id": "AI-UR-006", "status": "COMPLETE"},
    "socratic": {"task_id": "AI-UR-004", "status": "COMPLETE"},
    "tool_permission": {"task_id": "AI-UR-005", "status": "COMPLETE"},
    "artifacts": {"task_id": "AI-UR-003", "status": "COMPLETE"},
    "deep_research": {"task_id": "AI-UR-007", "status": "COMPLETE"},
    "coding_agent_draft_pr": {"task_id": "AI-UR-013", "status": "COMPLETE"},
}


def _git_sha(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def discover_owner_root(device_os_root: Path) -> Path | None:
    parents = [device_os_root.parent, device_os_root.parent.parent]
    for parent in parents:
        cand = parent / "gunnchAI3k"
        marker = cand / "artifacts" / "user-ready" / "AI_USER_READY_003_RESULT.json"
        if marker.is_file():
            return cand
        # Fall back to #34 artifact only if #35 is absent (should not happen on accepted tip).
        marker2 = cand / "artifacts" / "user-ready" / "AI_USER_READY_002_RESULT.json"
        if marker2.is_file():
            return cand
    return None


def consume_owner_matrix(device_os_root: Path, owner_root: Path | None = None) -> dict[str, Any]:
    root = Path(device_os_root).resolve()
    owner = Path(owner_root).resolve() if owner_root else discover_owner_root(root)
    if owner is None:
        return {
            "schema": SCHEMA,
            "ok": False,
            "error": "gunnchai_owner_root_missing",
            "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
        }

    result_003 = owner / "artifacts" / "user-ready" / "AI_USER_READY_003_RESULT.json"
    result_002 = owner / "artifacts" / "user-ready" / "AI_USER_READY_002_RESULT.json"
    result_path = result_003 if result_003.is_file() else result_002
    mastery_path = owner / "artifacts" / "waike-mastery" / "AI_WAIKE_MASTERY_EVAL.json"
    if not result_path.is_file():
        return {
            "schema": SCHEMA,
            "ok": False,
            "error": "gunnchai_owner_result_missing",
            "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
            "owner_root": str(owner),
        }

    doc = json.loads(result_path.read_text(encoding="utf-8"))
    cov = doc.get("coverage") or {}
    complete = list(cov.get("complete_ids") or COMPLETE_IDS)
    partial = list(cov.get("partial_ids") or PARTIAL_IDS)
    open_ids = list(cov.get("open_ids") or OPEN_IDS)

    # Prefer-fail honesty: refuse to promote PARTIAL/OPEN into COMPLETE for UI.
    ui_claims = {
        tid: "COMPLETE"
        for tid in complete
        if tid not in partial and tid not in open_ids
    }
    for tid in partial:
        ui_claims[tid] = "PARTIAL"
    for tid in open_ids:
        ui_claims[tid] = "OPEN"

    tokens = doc.get("tokens") or {}
    product_complete = bool(tokens.get("GUNNCHAI_APP_PRODUCT_COMPLETE"))
    if product_complete and (partial or open_ids):
        # Owner may set token false; enforce device-os UI never claims full COMPLETE.
        product_complete = False

    mastery: dict[str, Any] = {"ok": False, "present": False}
    if mastery_path.is_file():
        try:
            mdoc = json.loads(mastery_path.read_text(encoding="utf-8"))
            mastery = {
                "ok": True,
                "present": True,
                "path": str(mastery_path.relative_to(owner)),
                "WAIKE_AI_DIGITAL_MASTERY_PASS": bool(mdoc.get("WAIKE_AI_DIGITAL_MASTERY_PASS")),
                "AI_WAIKE_MASTERY_INFRA_SMOKE_PASS": bool(mdoc.get("AI_WAIKE_MASTERY_INFRA_SMOKE_PASS")),
                "open": bool(mdoc.get("open")),
                "children": mdoc.get("children"),
                "note": "Mastery sidecar from accepted #37. Does not invent COMPLETE for #36 OPEN surfaces.",
            }
        except json.JSONDecodeError:
            mastery = {"ok": False, "present": True, "error": "mastery_json_invalid"}

    out = {
        "schema": SCHEMA,
        "ok": True,
        "owner_root": str(owner),
        "owner_commit": _git_sha(owner),
        "owner_result_path": str(result_path.relative_to(owner))
        if result_path.is_relative_to(owner)
        else str(result_path),
        "packet": doc.get("packet"),
        "accepted_main_pr": 37,
        "refused_unmerged_pr": 36,
        "counts": {
            "COMPLETE": len(complete),
            "PARTIAL": len(partial),
            "OPEN": len(open_ids),
        },
        "complete_ids": complete,
        "partial_ids": partial,
        "open_ids": open_ids,
        "ui_claims": ui_claims,
        "persona_safe_capabilities": PERSONA_SAFE_CAPABILITIES,
        "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
        "AI_USER_READY_002_DIGITAL_PASS": bool(tokens.get("AI_USER_READY_002_DIGITAL_PASS")),
        "AI_USER_READY_003_DIGITAL_PASS": bool(tokens.get("AI_USER_READY_003_DIGITAL_PASS")),
        "NANO_FALLBACK_ONLY": bool(tokens.get("NANO_FALLBACK_ONLY")),
        "model_tiers": doc.get("modelTiers"),
        "waike_mastery": mastery,
        "honesty_rule": (
            "Product UI must not claim COMPLETE for PARTIAL/OPEN. "
            "Personas may use Local Fast, Projects/memory, source-grounded, "
            "Socratic, tool permission, artifacts, deep research, coding DRAFT PR — "
            "COMPLETE-class after #35. Vision/OCR remains PARTIAL. "
            "Tutor/mastery entry consumes #37 sidecar only; never unmerged #36."
        ),
        "claim_boundary": (
            "Consumed from gunnchAI3k accepted main tip (#37 mastery + #35 honesty matrix). "
            "Unmerged #36 refused. Not frontier parity. Cursor does not merge."
        ),
    }

    # Integrity check vs expected 9/1/6 after #35
    expected = (9, 1, 6)
    actual = (len(complete), len(partial), len(open_ids))
    out["matrix_matches_9_1_6"] = actual == expected
    out["matrix_matches_7_3_6"] = False  # superseded by #35; keep key for old readers
    if not out["matrix_matches_9_1_6"]:
        out["ok"] = False
        out["error"] = f"matrix_count_mismatch:expected_{expected}:got_{actual}"
    return out


def write_consume_artifact(device_os_root: Path, payload: dict[str, Any]) -> Path:
    out_dir = Path(device_os_root) / "artifacts" / "product_use"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "GUNNCHAI_HONESTY_CONSUMED.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
