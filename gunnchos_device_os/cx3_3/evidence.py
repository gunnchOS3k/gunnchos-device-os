"""Write CX3.3 evidence under artifacts/complete_experience/cx3_3/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx3_3 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx3_3.audit import pick_next_gate
from gunnchos_device_os.cx3_3.foundation import finalize_matrices
from gunnchos_device_os.cx3_3.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx3_3.tokens import Cx33Tokens


def write_evidence(repo: Optional[Path], tokens: Cx33Tokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    mirror = Path("/tmp/cx3_3_evidence")
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
    tokens.CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS = bool(tokens.digital_closure_eligible())

    tok = tokens.to_dict()
    # Matrices depend on final tokens
    matrices = finalize_matrices(repo, tok)
    facts.update(matrices)
    # Recompute closure if blockers A non-empty
    blockers = matrices.get("CX3_3_BLOCKER_REGISTER") or {}
    if int(blockers.get("automatable_digital_count") or 0) > 0:
        tokens.CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS = False
        tok = tokens.to_dict()

    next_gate = pick_next_gate(tok)
    dump("CX3_3_TOKENS.json", tok)

    mapping = {
        "CX3_3_PROVENANCE_REBIND": "CX3_3_PROVENANCE_REBIND.json",
        "CX3_3_WAIKE_RELEASE_DEPENDENCY_DISCOVERY": "CX3_3_WAIKE_RELEASE_DEPENDENCY_DISCOVERY.json",
        "CX3_3_REAL_WAIKE_EARNED_CREDENTIAL": "CX3_3_REAL_WAIKE_EARNED_CREDENTIAL.json",
        "CX3_3_EDUCATION_TIMELINE": "CX3_3_EDUCATION_TIMELINE.json",
        "CX3_3_SKILL_EVIDENCE_GRAPH": "CX3_3_SKILL_EVIDENCE_GRAPH.json",
        "CX3_3_CAREER_PACKAGE": "CX3_3_CAREER_PACKAGE.json",
        "CX3_3_CAREER_PACKAGE_RECOVERY": "CX3_3_CAREER_PACKAGE_RECOVERY.json",
        "CX3_3_VERIFIER_MATRIX": "CX3_3_VERIFIER_MATRIX.json",
        "CX3_3_AUTOMATED_A11Y": "CX3_3_AUTOMATED_A11Y.json",
        "CX3_3_NO_SECOND_COMPUTER_FINAL": "CX3_3_NO_SECOND_COMPUTER_FINAL.json",
        "CX3_3_SECURITY_AUDIT": "CX3_3_SECURITY_AUDIT.json",
        "CX3_3_EDUCATION_CAREER_DOMAIN_MATRIX": "CX3_3_EDUCATION_CAREER_DOMAIN_MATRIX.json",
        "CX3_3_BLOCKER_REGISTER": "CX3_3_BLOCKER_REGISTER.json",
        "CX3_3_CX_STACK_MERGE_READINESS": "CX3_3_CX_STACK_MERGE_READINESS.json",
        "CX3_3_GUI_JOURNEY": "CX3_3_GUI_JOURNEY.json",
    }
    for key, fname in mapping.items():
        if key in facts:
            dump(fname, facts[key])

    for key, obj in facts.items():
        if key.startswith("CX3_3_") and key not in mapping and isinstance(obj, (dict, list)):
            dump(f"{key}.json", obj)

    remediation = {
        "schema": "gunnchos.cx3_3.remediation_summary.v1",
        "cycles_used": facts.get("remediation_cycles") or 0,
        "max_cycles_per_blocker": 3,
        "notes": facts.get("remediation_notes") or [],
        "certification_claimed": False,
    }
    dump("CX3_3_REMEDIATION_SUMMARY.json", remediation)

    verdict = {
        "schema": "gunnchos.cx3_3.education_career_digital_closure_verdict.v1",
        "generated_at_utc": generated,
        "CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS": tokens.CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS,
        "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": tokens.CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS,
        "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": tokens.WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "certification_claimed": False,
        "NEXT_CX_GATE": next_gate,
        "tokens": tok,
        "blocker_register_A_count": blockers.get("automatable_digital_count"),
    }
    dump("CX3_3_EDUCATION_CAREER_DIGITAL_CLOSURE_VERDICT.json", verdict)

    report = {
        "schema": "gunnchos.cx3_3.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX3.3",
        "tokens": tok,
        "firewall": {
            "device_lab_134_unaltered": tokens.CX3_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX3_PORTAL_14_UNALTERED and tokens.CX3_PORTAL_15_UNALTERED,
            "waike_release_unaltered": tokens.CX3_WAIKE_RELEASE_UNALTERED,
            "no_device_lab": tokens.CX3_NO_DEVICE_LAB,
            "evidence_path": "artifacts/complete_experience/cx3_3",
            "lab_path": "os_build/cx3_3_linux_lab",
            "no_merges": tokens.CX3_NO_MERGES,
            "certification_claimed": False,
        },
        "NEXT_CX_GATE": next_gate,
        "lab_blocker": tokens.lab_blocker,
        "waike_blocker": tokens.waike_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX3_3_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX3.3 evidence\n\n"
        "Education/Career digital closure + conditional WAIKE retry.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "`certification_claimed=false` always.\n"
        "Evidence only under `artifacts/complete_experience/cx3_3/`.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
