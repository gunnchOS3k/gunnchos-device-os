"""CX3.3 provenance rebind — retain CX3.1 + CX3.2 truth without full historical reruns."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple

# Map prompt-facing aliases → stored CX3.1 evidence keys
_CX31_ALIAS_MAP = {
    "CX3_REAL_SIGNED_ISSUER_PASS": "CX3_LAB_ISSUER_ED25519_PASS",
    "CX3_REAL_EVIDENCE_BOUND_ISSUANCE_PASS": "CX3_EVIDENCE_BOUND_ISSUANCE_PASS",
    "CX3_WALLET_SECURE_STORAGE_PASS": "CX3_WALLET_STORAGE_PASS",
    "CX3_REAL_WALLET_GUI_PASS": "CX3_WALLET_GUI_PASS",
    "CX3_REAL_SIGNED_CREDENTIAL_JOURNEY_PASS": "CX3_SIGNED_CREDENTIAL_JOURNEY_PASS",
    "CX3_TAMPER_DETECTION_PASS": "CX3_TAMPER_DETECT_PASS",
    "CX3_REVOCATION_STATUS_PASS": "CX3_REVOCATION_STATUS_PASS",
    "CX3_OFFLINE_VERIFY_PASS": "CX3_OFFLINE_VERIFY_PASS",
    "CX3_CREDENTIAL_IMPORT_EXPORT_PASS": "CX3_IMPORT_EXPORT_PASS",
    "CX3_REAL_PORTFOLIO_GUI_PASS": "CX3_PORTFOLIO_GUI_PASS",
    "CX3_PORTFOLIO_PRIVACY_PASS": "CX3_PORTFOLIO_PRIVACY_EXPORT_PASS",
    "CX3_PORTABLE_PORTFOLIO_EXPORT_PASS": "CX3_PORTFOLIO_PORTABLE_PACKAGE_PASS",
}

_CX32_REQUIRED = (
    "CX3_REAL_CAREER_PROFILE_GUI_PASS",
    "CX3_RESUME_EXPORT_PASS",
    "CX3_PORTFOLIO_SHARE_PACKAGE_PASS",
    "CX3_INDEPENDENT_VERIFIER_PASS",
    "CX3_REAL_VERIFIER_GUI_PASS",
    "CX3_SELECTIVE_DISCLOSURE_PASS",
    "CX3_VERIFIER_REVOCATION_PROPAGATION_PASS",
    "CX3_OFFLINE_CAREER_VERIFIER_PASS",
    "CX3_NO_SECOND_COMPUTER_CAREER_PASS",
    "CX3_2_SECURITY_REGRESSION_FREE",
)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def rebind_truth(repo: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (facts, token_hints) for CX3.1+CX3.2 retained truth."""
    cx3 = _load_json(repo / "artifacts" / "complete_experience" / "cx3" / "CX3_TOKENS.json")
    cx32 = _load_json(repo / "artifacts" / "complete_experience" / "cx3_2" / "CX3_2_TOKENS.json")
    cx32_verdict = _load_json(
        repo / "artifacts" / "complete_experience" / "cx3_2" / "CX3_2_CAREER_SHARING_VERIFIER_VERDICT.json"
    )

    retained: Dict[str, Any] = {}
    missing: list[str] = []
    false_tokens: list[str] = []

    # Foundation aggregate
    foundation = bool(cx3.get("CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS"))
    retained["CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS"] = foundation
    if not foundation:
        false_tokens.append("CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS")

    for alias, source in _CX31_ALIAS_MAP.items():
        val = bool(cx3.get(source))
        retained[alias] = val
        retained[source] = val
        if source not in cx3 and alias not in cx3:
            missing.append(source)
        if not val:
            false_tokens.append(alias)

    for key in _CX32_REQUIRED:
        val = bool(cx32.get(key))
        retained[key] = val
        if key not in cx32:
            missing.append(key)
        if not val:
            false_tokens.append(key)

    career_verifier = bool(cx32.get("CX3_2_CAREER_VERIFIER_PASS") or cx32_verdict.get("CX3_2_CAREER_VERIFIER_PASS"))
    retained["CX3_2_CAREER_VERIFIER_PASS"] = career_verifier
    if not career_verifier:
        false_tokens.append("CX3_2_CAREER_VERIFIER_PASS")

    # Journey classes from CX3.1
    for j in ("J1_CLASS", "J2_CLASS", "J3_CLASS", "J4_CLASS", "J5_CLASS", "J6_CLASS", "J7_CLASS"):
        if cx3.get(j):
            retained[j] = cx3[j]
        elif cx32.get(j):
            retained[j] = cx32[j]

    # WAIKE tokens retained honestly from CX3.2 (may be false)
    for k in (
        "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE",
        "CX3_WAIKE_READ_ONLY_PROVIDER_PASS",
        "CX3_WAIKE_EVIDENCE_PROVENANCE_PASS",
        "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS",
        "CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS",
    ):
        if k in cx32:
            retained[k] = bool(cx32[k])

    rebind_ok = (
        foundation
        and career_verifier
        and not missing
        and all(retained.get(a) for a in _CX31_ALIAS_MAP)
        and all(retained.get(k) for k in _CX32_REQUIRED)
        and cx3.get("FULL_COMPLETE_EXPERIENCE_COMPLETE") is not True
        and cx32.get("FULL_COMPLETE_EXPERIENCE_COMPLETE") is not True
        and cx3.get("CX3_CERTIFICATION_CLAIMED") is not True
        and cx32.get("CX3_CERTIFICATION_CLAIMED") is not True
    )

    facts = {
        "schema": "gunnchos.cx3_3.provenance_rebind.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "CX3_3_REBIND_PASS": rebind_ok,
        "retained": retained,
        "missing": missing,
        "false_tokens": false_tokens,
        "cx3_tokens_path": "artifacts/complete_experience/cx3/CX3_TOKENS.json",
        "cx32_tokens_path": "artifacts/complete_experience/cx3_2/CX3_2_TOKENS.json",
        "historical_journeys_rerun": False,
        "certification_claimed": False,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
    }
    hints = {k: v for k, v in retained.items() if isinstance(v, (bool, str))}
    hints["CX3_3_REBIND_PASS"] = rebind_ok
    return facts, hints
