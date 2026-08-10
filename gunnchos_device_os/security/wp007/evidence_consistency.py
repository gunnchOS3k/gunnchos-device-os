"""CI evidence consistency for WP-007 / WP-007R (Cycle 2).

Fails closed on contradictory readiness vs Independent RESULT claims.
Honest implementer_prepared / independent_verified=false states pass on DRAFT tips.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _git_sha(ref: str = "HEAD") -> str | None:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True)
            .strip()
        )
    except Exception:
        return None


def _git_merge_base_is_ancestor(sha: str, tip: str = "HEAD") -> bool:
    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", sha, tip],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def evaluate_evidence_consistency(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    violations: list[dict[str, str]] = []

    result_path = root / "artifacts/wp007/VP-007-RESULT.json"
    readiness_path = root / "artifacts/wp007/INTERNAL_RED_TEAM_READINESS.json"
    residual_path = root / "artifacts/wp007/IMPLEMENTER_RESIDUAL_STATUS.json"
    red_path = root / "artifacts/wp007/RED_TEAM_RESULTS.json"

    result = _load(result_path)
    readiness = _load(readiness_path)
    residual = _load(residual_path)
    red = _load(red_path)

    if result is None:
        violations.append(
            {
                "code": "MISSING_VP_RESULT",
                "detail": "artifacts/wp007/VP-007-RESULT.json missing",
            }
        )
        return _report(violations, result, readiness, residual)

    if readiness is None:
        violations.append(
            {
                "code": "MISSING_READINESS",
                "detail": "artifacts/wp007/INTERNAL_RED_TEAM_READINESS.json missing",
            }
        )

    overall = (result or {}).get("overall_result")
    ready_token = bool((readiness or {}).get("INTERNAL_RED_TEAM_READY"))
    independent_verified = bool((readiness or {}).get("independent_verified"))
    implementer_prepared = bool(
        (readiness or {}).get("implementer_prepared")
        or (readiness or {}).get("prepared_for_verifier")
    )
    production_ready = bool(
        (result or {}).get("production_ready")
        or (readiness or {}).get("production_ready")
        or (result or {}).get("claim_boundary", {}).get("production_ready")
    )
    external_pentest = (
        (readiness or {}).get("external_pentest")
        or (result or {}).get("external_pentest")
        or "EXTERNAL_PENDING"
    )
    evidence_level = str(
        (result or {}).get("evidence_level")
        or (readiness or {}).get("evidence_level")
        or ""
    )

    # 1) readiness=true while canonical VP result != PASS
    if ready_token and overall != "PASS":
        violations.append(
            {
                "code": "READINESS_TRUE_WITHOUT_PASS",
                "detail": (
                    f"INTERNAL_RED_TEAM_READY=true but VP-007-RESULT overall_result={overall!r}"
                ),
            }
        )
    if independent_verified and overall != "PASS":
        violations.append(
            {
                "code": "INDEPENDENT_VERIFIED_WITHOUT_PASS",
                "detail": "independent_verified=true requires overall_result=PASS",
            }
        )

    # 2) verifier SHA must be accepted/current permitted main when claiming independent ready
    tip_verified = (result or {}).get("tip_verified")
    head = _git_sha("HEAD")
    origin_main = _git_sha("origin/main") or _git_sha("main")
    if ready_token or independent_verified:
        if not tip_verified:
            violations.append(
                {
                    "code": "MISSING_TIP_VERIFIED",
                    "detail": "Independent ready claim requires tip_verified",
                }
            )
        else:
            permitted = {x for x in (head, origin_main) if x}
            # Also permit if tip_verified is ancestor of HEAD (merged) or equals HEAD
            ok_sha = tip_verified in permitted or (
                head is not None and _git_merge_base_is_ancestor(str(tip_verified), "HEAD")
            )
            if not ok_sha:
                violations.append(
                    {
                        "code": "VERIFIER_SHA_NOT_PERMITTED",
                        "detail": (
                            f"tip_verified={tip_verified} not HEAD/origin/main "
                            f"(head={head}, origin_main={origin_main})"
                        ),
                    }
                )

    # 3) open digital S0/S1
    s0 = int((result or {}).get("SECURITY_S0") or (red or {}).get("SECURITY_S0") or 0)
    s1 = int((result or {}).get("SECURITY_S1") or (red or {}).get("SECURITY_S1") or 0)
    if implementer_prepared or ready_token:
        if s0 > 0 or s1 > 0:
            violations.append(
                {
                    "code": "OPEN_DIGITAL_S0_S1",
                    "detail": f"SECURITY_S0={s0} SECURITY_S1={s1}",
                }
            )
        open_s0 = (red or {}).get("open_s0") or []
        open_s1 = (red or {}).get("open_s1") or []
        if open_s0 or open_s1:
            violations.append(
                {
                    "code": "OPEN_DIGITAL_S0_S1_CASES",
                    "detail": f"open_s0={open_s0} open_s1={open_s1}",
                }
            )

    # 4) open RESIDUAL_DIGITAL S2 hidden while readiness claimed
    residuals = list((result or {}).get("SECURITY_S2_residual") or [])
    open_digital = [
        r
        for r in residuals
        if str(r.get("status", "")).upper() in {"RESIDUAL_DIGITAL", "OPEN", "OPEN_DIGITAL"}
    ]
    if ready_token and open_digital:
        # Allow if implementer residual status marks them CLOSED_DIGITAL prepared
        # and readiness is only candidate — but ready_token true still fails if still residual
        closed_ids = set()
        if residual:
            for item in residual.get("residuals") or []:
                if str(item.get("status", "")).startswith("CLOSED"):
                    closed_ids.add(item.get("id"))
        still_open = [r for r in open_digital if r.get("id") not in closed_ids]
        if still_open:
            violations.append(
                {
                    "code": "HIDDEN_RESIDUAL_DIGITAL_WHILE_READY",
                    "detail": (
                        "INTERNAL_RED_TEAM_READY=true with open RESIDUAL_DIGITAL: "
                        + ", ".join(str(r.get("id")) for r in still_open)
                    ),
                }
            )

    # 5) production_ready without external evidence
    if production_ready:
        if str(external_pentest).upper() in {"EXTERNAL_PENDING", "", "NONE", "FALSE"}:
            violations.append(
                {
                    "code": "PRODUCTION_READY_WITHOUT_EXTERNAL",
                    "detail": "production_ready requires external evidence; pentest still EXTERNAL_PENDING",
                }
            )
        if "E7" not in evidence_level.upper() and str(external_pentest).upper() != "E7_PASS":
            violations.append(
                {
                    "code": "PRODUCTION_READY_WITHOUT_E7",
                    "detail": f"production_ready requires E7-class evidence; got {evidence_level!r}",
                }
            )

    # 6) external pentest claimed without E7
    claimed_pentest = str(external_pentest).upper()
    if claimed_pentest not in {
        "EXTERNAL_PENDING",
        "PENDING",
        "NONE",
        "FALSE",
        "NOT_EXECUTED",
        "PREPARED_NOT_EXECUTED",
    }:
        if "E7" not in evidence_level.upper() and "PASS" not in claimed_pentest:
            # Explicit pass-like claim without E7 evidence level
            if claimed_pentest in {"DONE", "COMPLETE", "EXECUTED", "TRUE"}:
                violations.append(
                    {
                        "code": "EXTERNAL_PENTEST_WITHOUT_E7",
                        "detail": f"external_pentest={external_pentest!r} without E7 evidence",
                    }
                )
        if claimed_pentest in {"PASS", "PASSED", "COMPLETE", "DONE"} and "E7" not in evidence_level.upper():
            violations.append(
                {
                    "code": "EXTERNAL_PENTEST_WITHOUT_E7",
                    "detail": f"external_pentest={external_pentest!r} requires evidence_level E7",
                }
            )

    return _report(violations, result, readiness, residual, head=head, origin_main=origin_main)


def _report(
    violations: list[dict[str, str]],
    result: dict[str, Any] | None,
    readiness: dict[str, Any] | None,
    residual: dict[str, Any] | None,
    *,
    head: str | None = None,
    origin_main: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": "gunnchos.wp007.evidence_consistency.v1",
        "ok": len(violations) == 0,
        "WP007_CANONICAL_EVIDENCE_CONTRADICTIONS": len(violations),
        "violations": violations,
        "head": head,
        "origin_main": origin_main,
        "overall_result": (result or {}).get("overall_result"),
        "INTERNAL_RED_TEAM_READY": (readiness or {}).get("INTERNAL_RED_TEAM_READY"),
        "implementer_prepared": (readiness or {}).get("implementer_prepared")
        or (readiness or {}).get("prepared_for_verifier"),
        "independent_verified": (readiness or {}).get("independent_verified"),
        "residual_status_present": residual is not None,
        "note": (
            "Honest DRAFT tip: implementer_prepared=true, independent_verified=false, "
            "INTERNAL_RED_TEAM_READY=false while RESULT=FAIL is consistent."
        ),
    }
