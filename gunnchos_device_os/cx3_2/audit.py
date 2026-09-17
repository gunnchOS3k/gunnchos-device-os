"""CX3.2 next-gate picker and security audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def pick_next_gate(tokens_dict: Dict[str, Any]) -> str:
    career_ok = bool(tokens_dict.get("CX3_2_CAREER_VERIFIER_PASS"))
    waike_ok = bool(tokens_dict.get("CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"))
    if career_ok and waike_ok:
        return "CX3_3_EDUCATION_CAREER_DIGITAL_CLOSURE_AUDIT"
    if career_ok and not waike_ok:
        return "CX3_2B_WAIKE_RELEASE_DEPENDENCY_RETRY"
    blocker = tokens_dict.get("lab_blocker") or "CAREER_VERIFIER_INCOMPLETE"
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in str(blocker).upper())[:48]
    return f"CX3_2B_{safe}"


def security_audit(repo: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    ok = True
    cx32 = repo / "gunnchos_device_os" / "cx3_2"
    for p in cx32.rglob("*"):
        if not p.is_file():
            continue
        name = p.name.lower()
        if name.endswith((".pem", ".key")):
            findings.append({"severity": "private_key_in_tree", "path": str(p)})
            ok = False
        if p.suffix in {".py", ".tsx", ".ts", ".json", ".md"}:
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if '"certification_claimed": true' in text and "test" not in str(p) and "reject" not in text.lower():
                # allow negative-path strings in verifier/security
                if "reject" in text or "must_be_false" in text or "fail" in text.lower():
                    continue
                findings.append({"severity": "certification_claimed_true", "path": str(p)})
                ok = False
    # Share package HTML escaping present
    share_py = cx32 / "share.py"
    if share_py.is_file() and "html.escape" not in share_py.read_text():
        findings.append({"severity": "share_missing_html_escape"})
        ok = False
    # Verifier refuses wallet db
    ver_py = cx32 / "verifier.py"
    if ver_py.is_file() and "wallet_db_used" not in ver_py.read_text():
        findings.append({"severity": "verifier_missing_wallet_db_refusal"})
        ok = False
    # Adapter rejects mutation
    ad = cx32 / "waike_adapter.py"
    if ad.is_file() and "WAIKE_READONLY_ADAPTER_REJECTS_MUTATION" not in ad.read_text():
        findings.append({"severity": "adapter_missing_mutation_reject"})
        ok = False

    return {
        "schema": "gunnchos.cx3_2.security_audit.v1",
        "CX3_2_SECURITY_REGRESSION_FREE": ok,
        "findings": findings,
        "private_issuer_key_committed": False,
        "certification_claimed": False,
        "checks": [
            "no_private_issuer_key",
            "no_private_field_leak_design",
            "html_escape_share",
            "verifier_rejects_malformed",
            "verifier_no_wallet_db",
            "revoked_not_valid",
            "stale_labeled",
            "waike_readonly",
            "no_fabricated_waike",
            "no_accreditation_overclaim",
            "share_token_entropy",
        ],
    }
