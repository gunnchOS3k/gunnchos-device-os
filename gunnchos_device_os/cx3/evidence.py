"""Write CX3.1 evidence under artifacts/complete_experience/cx3/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx3 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx3.audit import pick_next_gate
from gunnchos_device_os.cx3.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx3.tokens import Cx3Tokens


def write_evidence(
    repo: Optional[Path],
    tokens: Cx3Tokens,
    facts: Dict[str, Any],
) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    mirror = Path("/tmp/cx3_evidence")
    for d in (root, mirror):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    generated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def dump(name: str, obj: Any) -> None:
        text = json.dumps(obj, indent=2) + "\n"
        for d in (root, mirror):
            try:
                (d / name).write_text(text)
            except OSError:
                continue

    tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE = False
    tokens.CX3_CERTIFICATION_CLAIMED = False
    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    tokens.CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS = bool(tokens.foundation_eligible())

    tok = tokens.to_dict()
    next_gate = pick_next_gate(tok)
    dump("CX3_TOKENS.json", tok)

    for key, obj in facts.items():
        if isinstance(obj, (dict, list)) and (
            key.startswith("CX3_") or key.startswith("WAIKE_") or key in ("vault_bind", "foundation")
        ):
            dump(f"{key}.json" if not key.endswith(".json") else key, obj)

    verdict = {
        "schema": "gunnchos.cx3.wallet_portfolio_verdict.v1",
        "generated_at_utc": generated,
        "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": tokens.CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS,
        "WAIKE_INTEGRATION_SEAM_PASS": tokens.WAIKE_INTEGRATION_SEAM_PASS,
        "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": tokens.WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "certification_claimed": False,
        "NEXT_CX_GATE": next_gate,
        "tokens": tok,
    }
    dump("CX3_WALLET_PORTFOLIO_VERDICT.json", verdict)

    report = {
        "schema": "gunnchos.cx3.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX3.1",
        "tokens": tok,
        "firewall": {
            "device_lab_134_unaltered": tokens.CX3_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX3_PORTAL_14_UNALTERED and tokens.CX3_PORTAL_15_UNALTERED,
            "waike_release_unaltered": tokens.CX3_WAIKE_RELEASE_UNALTERED,
            "no_device_lab": tokens.CX3_NO_DEVICE_LAB,
            "evidence_path": "artifacts/complete_experience/cx3",
            "lab_path": "os_build/cx3_linux_lab",
            "no_merges": tokens.CX3_NO_MERGES,
            "certification_claimed": False,
        },
        "NEXT_CX_GATE": next_gate,
        "lab_blocker": tokens.lab_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX3_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX3.1 evidence\n\n"
        "Credential Wallet + Signed Portfolio Foundation.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "`certification_claimed=false` always — no accreditation claims.\n"
        "Evidence only under `artifacts/complete_experience/cx3/`.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
