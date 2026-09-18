"""CX3.3 domain matrix + blocker register + merge-readiness plan."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def _tip(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        return "unknown"


def build_domain_matrix(tokens: Dict[str, Any], tip: str) -> Dict[str, Any]:
    rows_spec = [
        ("Wallet", "CX3_REAL_WALLET_GUI_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Credential verification", "CX3_INDEPENDENT_VERIFIER_PASS", "digital", "CX3_3_VERIFIER_MATRIX.json"),
        ("Credential status/revocation", "CX3_VERIFIER_REVOCATION_PROPAGATION_PASS", "digital", "CX3_3_VERIFIER_MATRIX.json"),
        ("Evidence", "CX3_REAL_EVIDENCE_BOUND_ISSUANCE_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("WAIKE integration", "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS", "release", "CX3_3_WAIKE_RELEASE_DEPENDENCY_DISCOVERY.json"),
        ("Portfolio", "CX3_REAL_PORTFOLIO_GUI_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Career Profile", "CX3_REAL_CAREER_PROFILE_GUI_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Resume", "CX3_RESUME_EXPORT_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Share package", "CX3_PORTFOLIO_SHARE_PACKAGE_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Independent verifier", "CX3_INDEPENDENT_VERIFIER_PASS", "digital", "CX3_3_VERIFIER_MATRIX.json"),
        ("Selective disclosure", "CX3_SELECTIVE_DISCLOSURE_PASS", "digital", "CX3_3_VERIFIER_MATRIX.json"),
        ("Offline", "CX3_OFFLINE_CAREER_VERIFIER_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Import/export", "CX3_CREDENTIAL_IMPORT_EXPORT_PASS", "digital", "CX3_3_PROVENANCE_REBIND.json"),
        ("Recovery", "CX3_CAREER_PACKAGE_RECOVERY_PASS", "digital", "CX3_3_CAREER_PACKAGE_RECOVERY.json"),
        ("Education timeline", "CX3_EDUCATION_TIMELINE_PASS", "digital", "CX3_3_EDUCATION_TIMELINE.json"),
        ("Skill evidence graph", "CX3_SKILL_EVIDENCE_GRAPH_PASS", "digital", "CX3_3_SKILL_EVIDENCE_GRAPH.json"),
        ("Career package", "CX3_CAREER_PACKAGE_PASS", "digital", "CX3_3_CAREER_PACKAGE.json"),
        ("Accessibility automation", "CX3_AUTOMATED_A11Y_PASS", "digital", "CX3_3_AUTOMATED_A11Y.json"),
        ("Security", "CX3_3_SECURITY_REGRESSION_FREE", "digital", "CX3_3_SECURITY_AUDIT.json"),
        ("No-second-computer", "CX3_NO_SECOND_COMPUTER_FINAL_PASS", "digital", "CX3_3_NO_SECOND_COMPUTER_FINAL.json"),
    ]
    rows: List[Dict[str, Any]] = []
    for domain, token, default_class, artifact in rows_spec:
        val = bool(tokens.get(token))
        blocker = None
        blocker_class = None
        next_action = "retain"
        if domain == "WAIKE integration" and not val:
            blocker = tokens.get("waike_blocker") or "RELEASE_TRAIN_DEPENDENCY_PENDING"
            blocker_class = "release"
            next_action = "wait_for_waike_release_earned_evidence"
        elif domain == "Accessibility automation" and val:
            blocker = "HUMAN_VALIDATION_PENDING"
            blocker_class = "human"
            next_action = "schedule_human_a11y_study"
            # automated pass can be true while human pending
        elif not val and default_class == "digital":
            blocker = token
            blocker_class = "automatable_digital"
            next_action = "remediate_within_cx3_3"
        evidence_class = "PASS" if val else ("RELEASE_PENDING" if blocker_class == "release" else "FAIL")
        if domain == "Accessibility automation" and val:
            evidence_class = "AUTOMATED_PASS_HUMAN_PENDING"
        rows.append(
            {
                "domain": domain,
                "token": token,
                "token_value": val,
                "evidence_class": evidence_class,
                "artifact": artifact,
                "current_commit": tip,
                "blocker": blocker,
                "blocker_class": blocker_class,
                "next_action": next_action,
            }
        )
    return {
        "schema": "gunnchos.cx3_3.education_career_domain_matrix.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": rows,
        "certification_claimed": False,
    }


def build_blocker_register(tokens: Dict[str, Any]) -> Dict[str, Any]:
    a: List[Dict[str, Any]] = []
    b: List[Dict[str, Any]] = []
    c: List[Dict[str, Any]] = []
    d: List[Dict[str, Any]] = []
    e: List[Dict[str, Any]] = []

    digital_required = [
        "CX3_3_REBIND_PASS",
        "CX3_EDUCATION_TIMELINE_PASS",
        "CX3_SKILL_EVIDENCE_GRAPH_PASS",
        "CX3_CAREER_PACKAGE_PASS",
        "CX3_CAREER_PACKAGE_RECOVERY_PASS",
        "CX3_VERIFIER_MATRIX_PASS",
        "CX3_AUTOMATED_A11Y_PASS",
        "CX3_NO_SECOND_COMPUTER_FINAL_PASS",
        "CX3_3_SECURITY_REGRESSION_FREE",
        "CX3_2_CAREER_VERIFIER_PASS",
        "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS",
    ]
    for tok in digital_required:
        if not tokens.get(tok):
            a.append({"id": tok, "class": "A", "detail": "automatable digital blocker"})

    if not tokens.get("CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"):
        b.append(
            {
                "id": "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS",
                "class": "B",
                "detail": tokens.get("waike_blocker") or "RELEASE_TRAIN_DEPENDENCY_PENDING",
            }
        )

    c.extend(
        [
            {"id": "J6_HUMAN_A11Y_USER_STUDY", "class": "C", "detail": "accessibility user study"},
            {"id": "UX_VALIDATION", "class": "C", "detail": "UX validation"},
        ]
    )
    d.extend(
        [
            {"id": "PHYSICAL_DEVICE_BEHAVIOR", "class": "D", "detail": "physical device behavior"},
            {"id": "CAMERA_MIC_PRINTER", "class": "D", "detail": "camera/mic/printer hardware"},
            {"id": "PHYSICAL_INPUT_ERGONOMICS", "class": "D", "detail": "physical input/ergonomics"},
        ]
    )
    e.extend(
        [
            {"id": "INSTITUTIONAL_ISSUER_ONBOARDING", "class": "E", "detail": "institutional issuer onboarding"},
            {"id": "EMPLOYER_VERIFIER_ADOPTION", "class": "E", "detail": "employer verifier adoption"},
            {"id": "STANDARDS_CONFORMANCE_CERT", "class": "E", "detail": "standards conformance/certification"},
            {"id": "PUBLIC_HOSTING", "class": "E", "detail": "public hosting"},
            {"id": "LEGAL_PRIVACY_REVIEW", "class": "E", "detail": "legal/privacy review where applicable"},
        ]
    )

    return {
        "schema": "gunnchos.cx3_3.blocker_register.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "A_automatable_digital": a,
        "B_release_dependency": b,
        "C_human_pending": c,
        "D_physical_pending": d,
        "E_external_business_pending": e,
        "automatable_digital_count": len(a),
        "certification_claimed": False,
        "note": "Register is not emptied by shrinking end-state.",
    }


def build_merge_readiness(repo: Path, *, device_os_pr: Optional[int] = None, portal_pr: Optional[int] = None) -> Dict[str, Any]:
    tip = _tip(repo)
    device_stack = [
        {"pr": 145, "branch": "eng/cx2h-journey-digital-pass-closure", "role": "CX2H"},
        {"pr": 146, "branch": "eng/cx2h2-document-print-recovery-j1-j7", "role": "CX2H.2"},
        {"pr": 147, "branch": "eng/cx2h3-browser-mail-offline-j2-j5", "role": "CX2H.3"},
        {"pr": 148, "branch": "eng/cx2h4-p0-digital-closure-audit", "role": "CX2H.4"},
        {"pr": 149, "branch": "eng/cx3-credential-wallet-portfolio-foundation", "role": "CX3.1", "head": "33673b4c6bfde858df526bd4b0cddf36d450336f"},
        {"pr": 150, "branch": "eng/cx3-waike-career-sharing-verifier-campaign", "role": "CX3.2", "head": "47c860c97f6deae2bf83633863530da8dea94af8"},
        {
            "pr": device_os_pr,
            "branch": "eng/cx3-education-career-digital-closure",
            "role": "CX3.3",
            "head": tip,
            "base": "eng/cx3-waike-career-sharing-verifier-campaign",
        },
    ]
    portal_stack = [
        {"pr": 24, "branch": "docs/cx2h-journey-digital-pass-control", "role": "CX2H"},
        {"pr": 25, "branch": "docs/cx2h2-document-print-recovery-control", "role": "CX2H.2"},
        {"pr": 26, "branch": "docs/cx2h3-browser-mail-offline-control", "role": "CX2H.3"},
        {"pr": 27, "branch": "docs/cx2h4-p0-digital-closure-control", "role": "CX2H.4"},
        {"pr": 28, "branch": "docs/cx3-credential-wallet-portfolio-control", "role": "CX3.1", "head": "689d19ea5e97bc049978cc3c9c520b11e3700f55"},
        {"pr": 29, "branch": "docs/cx3-waike-career-sharing-verifier-control", "role": "CX3.2", "head": "19b4b40c414855f12022880e61e78832a9fd2299"},
        {
            "pr": portal_pr,
            "branch": "docs/cx3-education-career-digital-closure-control",
            "role": "CX3.3",
            "base": "docs/cx3-waike-career-sharing-verifier-control",
        },
    ]

    def enrich(stack: List[Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
        out = []
        for i, item in enumerate(stack):
            pred = stack[i - 1]["branch"] if i else None
            out.append(
                {
                    **item,
                    "draft": True,
                    "mergeable": False,  # plan only — do not assert live mergeability as merge authority
                    "dependency": pred,
                    "required_rebase_after_predecessor_merge": True if i else False,
                    "required_ci": ["unit", "fail_closed_cx_tests"],
                    "merge_method_recommendation": "merge commit",
                    "evidence_revalidation_required": True,
                    "kind": kind,
                    "no_merge_executed": True,
                }
            )
        return out

    return {
        "schema": "gunnchos.cx3_3.cx_stack_merge_readiness.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "plan_only": True,
        "merges_executed": False,
        "device_os_stack": enrich(device_stack, "device_os"),
        "portal_stack": enrich(portal_stack, "portal"),
        "order": {
            "device_os": "#145 → #146 → #147 → #148 → #149 → #150 → CX3.3",
            "portal": "#24 → #25 → #26 → #27 → #28 → #29 → CX3.3",
        },
        "certification_claimed": False,
    }
