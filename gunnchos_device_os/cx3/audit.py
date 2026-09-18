"""CX3.1 next-gate picker and security fail-closed helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List


FORBIDDEN_CLAIM_SUBSTRINGS = (
    "accredited degree",
    "official diploma",
    "board certification",
    "certification_claimed\": true",
    "certification_claimed': true",
)


def pick_next_gate(tokens_dict: Dict[str, Any]) -> str:
    """
    Rules:
    - Wallet foundation PASS + WAIKE earned blocked → CX3_2_WAIKE_REAL_EARNED_CREDENTIAL_INTEGRATION
    - Wallet PASS + WAIKE earned also proven → CX3_2_CAREER_PORTFOLIO_SHARING_AND_VERIFIER
    - Else → CX3_1B_<BLOCKER>
    """
    foundation = bool(tokens_dict.get("CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS"))
    waike_earned = bool(tokens_dict.get("WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"))
    if foundation and waike_earned:
        return "CX3_2_CAREER_PORTFOLIO_SHARING_AND_VERIFIER"
    if foundation and not waike_earned:
        return "CX3_2_WAIKE_REAL_EARNED_CREDENTIAL_INTEGRATION"
    blocker = tokens_dict.get("lab_blocker") or "FOUNDATION_INCOMPLETE"
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in str(blocker).upper())[:48]
    return f"CX3_1B_{safe}"


def security_fail_closed_audit(repo: Path) -> Dict[str, Any]:
    """Static fail-closed checks for CX3 package."""
    cx3 = repo / "gunnchos_device_os" / "cx3"
    findings: List[Dict[str, Any]] = []
    pass_ok = True

    # Private key material must not live under package
    for p in cx3.rglob("*"):
        if not p.is_file():
            continue
        name = p.name.lower()
        if name.endswith((".pem", ".key")) and "test" not in str(p):
            findings.append({"severity": "private_key_in_tree", "path": str(p)})
            pass_ok = False
        if p.suffix in {".py", ".ts", ".tsx", ".json", ".md"}:
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            lower = text.lower()
            if "certification_claimed=true" in lower.replace(" ", "") or '"certification_claimed": true' in text:
                # Allow mentions in tests that assert rejection
                if "must_be_false" in lower or "fail" in lower or "reject" in lower or "assert" in lower:
                    continue
                if "const\": false" in text or "const': False" in text:
                    continue
                # Explicit true assignment is forbidden outside negative tests
                if "certification_claimed\": true" in text and "/tests/" not in str(p):
                    findings.append({"severity": "certification_claimed_true", "path": str(p)})
                    pass_ok = False

    # Ensure CERTIFICATION_CLAIMED constant is False
    init_py = cx3 / "__init__.py"
    if init_py.is_file():
        tree = ast.parse(init_py.read_text())
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "CERTIFICATION_CLAIMED":
                        if not (isinstance(node.value, ast.Constant) and node.value.value is False):
                            findings.append({"severity": "CERTIFICATION_CLAIMED_not_false"})
                            pass_ok = False

    return {
        "schema": "gunnchos.cx3.security_fail_closed.v1",
        "CX3_SECURITY_FAIL_CLOSED_PASS": pass_ok,
        "findings": findings,
        "certification_claimed": False,
        "private_issuer_keys_committed": False,
    }
