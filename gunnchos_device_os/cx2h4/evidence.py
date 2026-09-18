"""Write CX2H.4 evidence under artifacts/complete_experience/cx2h4/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2h4 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2h4.audit import pick_next_gate
from gunnchos_device_os.cx2h4.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h4.tokens import Cx2h4Tokens


def write_evidence(
    repo: Optional[Path],
    tokens: Cx2h4Tokens,
    facts: Dict[str, Any],
    *,
    matrix: Dict[str, Any],
    rebind: Dict[str, Any],
    j4: Dict[str, Any],
    office: Dict[str, Any],
    media: Dict[str, Any],
    developer: Dict[str, Any],
    nsc: Dict[str, Any],
    security: Dict[str, Any],
    blockers: Dict[str, Any],
) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    mirror = Path("/tmp/cx2h4_evidence")
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
    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    if j4.get("J4_CLASS"):
        tokens.J4_CLASS = j4["J4_CLASS"]
    tokens.CX2H4_J4_P0_DIGITAL_BLOCKER = bool(j4.get("J4_P0_DIGITAL_BLOCKER", True))
    tokens.CX2H4_SPREADSHEET_P0_PASS = bool(office.get("CX2H4_SPREADSHEET_P0_PASS"))
    tokens.CX2H4_PRESENTATION_P0_PASS = bool(office.get("CX2H4_PRESENTATION_P0_PASS"))
    tokens.CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS = str(media.get("CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS", "not_required"))
    tokens.CX2H4_DEVELOPER_BASELINE_PASS = str(developer.get("CX2H4_DEVELOPER_BASELINE_PASS", "not_required"))
    tokens.CX2H4_NO_SECOND_COMPUTER_P0_PASS = bool(nsc.get("CX2H4_NO_SECOND_COMPUTER_P0_PASS"))
    tokens.CX2H4_SECURITY_REGRESSION_FREE = bool(security.get("CX2H4_SECURITY_REGRESSION_FREE"))
    tokens.CX2H4_JOURNEY_REBIND_PASS = bool(rebind.get("CX2H4_JOURNEY_REBIND_PASS"))
    tokens.CX2H4_P0_DIGITAL_CLOSURE_PASS = bool(
        tokens.digital_closure_eligible() and not (blockers.get("blocks_cx3_count") or 0)
    )
    # Fail closed: any blocks_cx3 entry denies closure
    if blockers.get("blocks_cx3"):
        tokens.CX2H4_P0_DIGITAL_CLOSURE_PASS = False

    dump("CX2H4_DOMAIN_CLOSURE_MATRIX.json", matrix)
    dump("CX2H4_JOURNEY_PROVENANCE_REBIND.json", rebind)
    dump("CX2H4_J4_GAP_AUDIT.json", j4)
    dump("CX2H4_OFFICE_BREADTH_AUDIT.json", office)
    dump("CX2H4_MEDIA_PLAYBACK_AUDIT.json", media)
    dump("CX2H4_DEVELOPER_BASELINE_AUDIT.json", developer)
    dump("CX2H4_NO_SECOND_COMPUTER_DEPENDENCY.json", nsc)
    dump("CX2H4_SECURITY_REGRESSION_AUDIT.json", security)
    dump("CX2H4_P0_BLOCKER_REGISTER.json", blockers)

    tok = tokens.to_dict()
    dump("CX2H4_TOKENS.json", tok)
    verdict = {
        "schema": "gunnchos.cx2h4.digital_closure_verdict.v1",
        "generated_at_utc": generated,
        "CX2H4_P0_DIGITAL_CLOSURE_PASS": tokens.CX2H4_P0_DIGITAL_CLOSURE_PASS,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "blocks_cx3_count": blockers.get("blocks_cx3_count"),
        "NEXT_CX_GATE": pick_next_gate(tok, blockers),
        "tokens": tok,
    }
    dump("CX2H4_DIGITAL_CLOSURE_VERDICT.json", verdict)

    for key, obj in facts.items():
        if key.startswith("CX2H4_") and isinstance(obj, (dict, list)):
            dump(f"{key}.json", obj)

    report = {
        "schema": "gunnchos.cx2h4.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX2H.4",
        "tokens": tok,
        "firewall": {
            "device_lab_134_unaltered": tokens.CX2H_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX2H_PORTAL_14_UNALTERED and tokens.CX2H_PORTAL_15_UNALTERED,
            "device_lab_manifest_unaltered": tokens.CX2H_DEVICE_LAB_MANIFEST_UNALTERED,
            "evidence_path": "artifacts/complete_experience/cx2h4",
            "lab_path": "os_build/cx2h4_linux_lab",
            "no_merges": tokens.CX2H_NO_MERGES,
        },
        "NEXT_CX_GATE": verdict["NEXT_CX_GATE"],
        "lab_blocker": tokens.lab_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX2H4_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX2H.4 evidence\n\n"
        "P0 digital closure audit before CX3.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "Do not start CX3 unless `CX2H4_P0_DIGITAL_CLOSURE_PASS=true`.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
