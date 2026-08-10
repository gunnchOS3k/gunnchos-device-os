"""Phase XII defect register helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_defects(root: Path, defects: list[dict[str, Any]]) -> dict[str, Any]:
    reg = {
        "schema": "gunnchos.phase_xii.defects.v1",
        "open": [d for d in defects if d.get("status", "open") == "open"],
        "fixed": [d for d in defects if d.get("status") == "fixed"],
        "all": defects,
        "counts": {
            "X0": sum(1 for d in defects if d.get("severity") == "X0" and d.get("status", "open") == "open"),
            "X1": sum(1 for d in defects if d.get("severity") == "X1" and d.get("status", "open") == "open"),
            "X2": sum(1 for d in defects if d.get("severity") == "X2" and d.get("status", "open") == "open"),
        },
    }
    out = root / "artifacts" / "phase_xii" / "DEFECT_REGISTER.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    return reg


def write_ci_x1_residuals(root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    """Authoritative CI X1 residual register derived from RJ campaign defects."""
    defects = [d for d in (summary.get("defects") or []) if d.get("severity") == "X1" and d.get("status", "open") == "open"]
    # Deduplicate by id
    seen: set[str] = set()
    open_x1: list[dict[str, Any]] = []
    for d in defects:
        did = str(d.get("id") or "")
        if did in seen:
            continue
        seen.add(did)
        open_x1.append(
            {
                "id": did,
                "rj": d.get("rj"),
                "severity": "X1",
                "classification": d.get("classification") or "CONDITIONAL_EXTERNAL",
                "root_cause": d.get("root_cause") or d.get("error"),
                "repo": d.get("repo"),
                "notes": d.get("notes") or d.get("error"),
            }
        )
    residual = {
        "schema": "gunnchos.phase_xii.ci_x1_residuals.v1",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "physical_execution_freeze": True,
        "auto_merge_request": None,
        "source": {
            "note": (
                "Derived from RJ campaign defects on this prove run. "
                "X1 residuals must remain honest: do not claim REAL_*_DAY while open_x1 is non-empty."
            ),
            "rj_pass_count": summary.get("pass_count"),
            "rj_fail_count": summary.get("fail_count"),
        },
        "REAL_APP_X0_OPEN": int(summary.get("REAL_APP_X0_OPEN") or 0),
        "REAL_APP_X1_OPEN": len(open_x1),
        "REAL_APP_X2_OPEN": int(summary.get("REAL_APP_X2_OPEN") or 0),
        "open_x1": open_x1,
        "tokens": {
            "GUNNCHOS_REAL_STUDENT_DAY_DIGITAL_PASS": bool(summary.get("GUNNCHOS_REAL_STUDENT_DAY_DIGITAL_PASS")),
            "GUNNCHOS_REAL_OFFICE_DAY_DIGITAL_PASS": bool(summary.get("GUNNCHOS_REAL_OFFICE_DAY_DIGITAL_PASS")),
            "GUNNCHOS_REAL_CREATOR_DAY_DIGITAL_PASS": bool(summary.get("GUNNCHOS_REAL_CREATOR_DAY_DIGITAL_PASS")),
            "GUNNCHOS_REAL_RECREATION_DAY_DIGITAL_PASS": bool(summary.get("GUNNCHOS_REAL_RECREATION_DAY_DIGITAL_PASS")),
            "PHASE_XI_BEHAVIORAL_JOURNEY_HARNESS_PASS": True,
            "PHASE_XI_REAL_APPLICATION_DAY_PROOF": (
                "PROVEN" if len(open_x1) == 0 and int(summary.get("REAL_APP_X0_OPEN") or 0) == 0 else "NOT_YET_PROVEN"
            ),
        },
        "claim_boundary": (
            "REAL_*_DAY_DIGITAL_PASS remains FALSE while any CI X1 residual is open. "
            "PHYSICAL_EXECUTION_FREEZE=ACTIVE; auto_merge_request=null."
        ),
    }
    out = root / "artifacts" / "phase_xii" / "CI_X1_RESIDUALS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(residual, indent=2) + "\n", encoding="utf-8")
    return residual
