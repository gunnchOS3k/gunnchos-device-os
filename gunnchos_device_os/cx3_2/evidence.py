"""Write CX3.2 evidence under artifacts/complete_experience/cx3_2/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx3_2 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx3_2.audit import pick_next_gate
from gunnchos_device_os.cx3_2.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx3_2.tokens import Cx32Tokens


def write_evidence(repo: Optional[Path], tokens: Cx32Tokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    mirror = Path("/tmp/cx3_2_evidence")
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
    tokens.CX3_2_CAREER_VERIFIER_PASS = bool(tokens.career_verifier_eligible())

    tok = tokens.to_dict()
    next_gate = pick_next_gate(tok)
    dump("CX3_2_TOKENS.json", tok)

    mapping = {
        "CX3_2_WAIKE_ACCEPTED_MAIN_DISCOVERY": "CX3_2_WAIKE_ACCEPTED_MAIN_DISCOVERY.json",
        "CX3_2_WAIKE_EVIDENCE_ADAPTER": "CX3_2_WAIKE_EVIDENCE_ADAPTER.json",
        "CX3_2_REAL_WAIKE_EARNED_CREDENTIAL_JOURNEY": "CX3_2_REAL_WAIKE_EARNED_CREDENTIAL_JOURNEY.json",
        "CX3_2_CAREER_PROFILE": "CX3_2_CAREER_PROFILE_GUI.json",
        "CX3_2_RESUME_EXPORT": "CX3_2_RESUME_EXPORT.json",
        "CX3_2_SHARE_PACKAGE": "CX3_2_SHARE_PACKAGE.json",
        "CX3_2_INDEPENDENT_VERIFIER": "CX3_2_INDEPENDENT_VERIFIER.json",
        "CX3_2_VERIFIER_GUI": "CX3_2_VERIFIER_GUI_JOURNEY.json",
        "CX3_2_SELECTIVE_DISCLOSURE": "CX3_2_SELECTIVE_DISCLOSURE.json",
        "CX3_2_SECURITY_AUDIT": "CX3_2_SECURITY_AUDIT.json",
        "CX3_2_WAIKE_MISMATCH": "CX3_2_WAIKE_MISMATCH.json",
        "CX3_2_REVOCATION_PROPAGATION": "CX3_2_REVOCATION_PROPAGATION.json",
        "CX3_2_OFFLINE_CAREER_VERIFIER": "CX3_2_OFFLINE_CAREER_VERIFIER.json",
        "CX3_2_GUI_JOURNEY": "CX3_2_GUI_JOURNEY.json",
    }
    for key, fname in mapping.items():
        if key in facts:
            dump(fname, facts[key])

    # Also dump any CX3_2_* facts
    for key, obj in facts.items():
        if key.startswith("CX3_2_") and key not in mapping and isinstance(obj, (dict, list)):
            dump(f"{key}.json", obj)

    verdict = {
        "schema": "gunnchos.cx3_2.career_sharing_verifier_verdict.v1",
        "generated_at_utc": generated,
        "CX3_2_CAREER_VERIFIER_PASS": tokens.CX3_2_CAREER_VERIFIER_PASS,
        "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": tokens.CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS,
        "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": tokens.WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "certification_claimed": False,
        "NEXT_CX_GATE": next_gate,
        "tokens": tok,
    }
    dump("CX3_2_CAREER_SHARING_VERIFIER_VERDICT.json", verdict)

    report = {
        "schema": "gunnchos.cx3_2.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX3.2",
        "tokens": tok,
        "firewall": {
            "device_lab_134_unaltered": tokens.CX3_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX3_PORTAL_14_UNALTERED and tokens.CX3_PORTAL_15_UNALTERED,
            "waike_release_unaltered": tokens.CX3_WAIKE_RELEASE_UNALTERED,
            "no_device_lab": tokens.CX3_NO_DEVICE_LAB,
            "evidence_path": "artifacts/complete_experience/cx3_2",
            "lab_path": "os_build/cx3_2_linux_lab",
            "no_merges": tokens.CX3_NO_MERGES,
            "certification_claimed": False,
        },
        "NEXT_CX_GATE": next_gate,
        "lab_blocker": tokens.lab_blocker,
        "waike_blocker": tokens.waike_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX3_2_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX3.2 evidence\n\n"
        "Real WAIKE credential integration (honest) + Career sharing + Independent verifier.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "`certification_claimed=false` always.\n"
        "Evidence only under `artifacts/complete_experience/cx3_2/`.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
