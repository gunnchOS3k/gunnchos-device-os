"""Write CX2H evidence under artifacts/complete_experience/cx2h/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2h import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2h.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h.tokens import Cx2hTokens


def next_gate(tokens: Cx2hTokens) -> str:
    if tokens.J3_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS" and tokens.CX2H_XDG_PORTAL_SESSION_PASS:
        return "CX2H2_DOCUMENT_PRINT_RECOVERY_J1_J7"
    if tokens.J3_CLASS == "REAL_PROVIDER_GUI_PARTIAL":
        frag = (tokens.lab_blocker or "APP_LAUNCH_GUI").split(":")[0].strip().replace(" ", "_")[:80]
        if frag.startswith("CX2H_"):
            frag = frag[5:]
        return "CX2H1C_" + frag
    if tokens.lab_blocker:
        frag = tokens.lab_blocker.split(":")[0].strip().replace(" ", "_")[:80]
        if frag.startswith("CX2H_"):
            return "CX2H1_" + frag[5:]
        return "CX2H1_" + frag
    if not tokens.gate_shell_prereq():
        return "CX2H1_SHELL_PREREQ"
    if not tokens.CX2H_XDG_PORTAL_SESSION_PASS:
        return "CX2H1_XDG_PORTAL_SESSION"
    if tokens.J3_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        return "CX2H1_J3_APP_CENTER"
    return "CX2H2_DOCUMENT_PRINT_RECOVERY_J1_J7"


def write_evidence(repo: Optional[Path], tokens: Cx2hTokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    # Mirror under /tmp so sandboxed hosts that cannot write Downloads/ still retain evidence.
    mirror = Path("/tmp/cx2h1b_evidence")
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

    if "CX2H_PORTAL_ROOT_CAUSE" in facts:
        dump("CX2H_PORTAL_ROOT_CAUSE.json", facts["CX2H_PORTAL_ROOT_CAUSE"])
    if "CX2H_XDG_PORTAL_MATRIX" in facts:
        dump("CX2H_XDG_PORTAL_MATRIX.json", facts["CX2H_XDG_PORTAL_MATRIX"])
    if "CX2H_FLATPAK_REPO_PROVENANCE" in facts:
        dump("CX2H_FLATPAK_REPO_PROVENANCE.json", facts["CX2H_FLATPAK_REPO_PROVENANCE"])
    if "CX2H_J3_APP_CENTER_JOURNEY" in facts:
        dump("CX2H_J3_APP_CENTER_JOURNEY.json", facts["CX2H_J3_APP_CENTER_JOURNEY"])
    if "CX2H_SHELL_PREREQ" in facts:
        dump("CX2H_SHELL_PREREQ.json", facts["CX2H_SHELL_PREREQ"])
    if "FRAMEBUFFER_DIFF_REPORT" in facts:
        dump("FRAMEBUFFER_DIFF_REPORT.json", facts["FRAMEBUFFER_DIFF_REPORT"])
    if "CX2H_FRAMEBUFFER_CAPTURE_MANIFEST" in facts:
        dump("CX2H_FRAMEBUFFER_CAPTURE_MANIFEST.json", facts["CX2H_FRAMEBUFFER_CAPTURE_MANIFEST"])
    if "CX2H1B_J3_EVIDENCE_REVIEW" in facts:
        dump("CX2H1B_J3_EVIDENCE_REVIEW.json", facts["CX2H1B_J3_EVIDENCE_REVIEW"])
    if "CX2H1B_FLATPAK_LAUNCH_ROOT_CAUSE" in facts:
        dump("CX2H1B_FLATPAK_LAUNCH_ROOT_CAUSE.json", facts["CX2H1B_FLATPAK_LAUNCH_ROOT_CAUSE"])
    if "CX2H1B_WINDOW_PROOF_V1" in facts:
        dump("CX2H1B_WINDOW_PROOF_V1.json", facts["CX2H1B_WINDOW_PROOF_V1"])
    if "CX2H1B_WINDOW_PROOF_V2" in facts:
        dump("CX2H1B_WINDOW_PROOF_V2.json", facts["CX2H1B_WINDOW_PROOF_V2"])
    if "CX2H1B_PROVIDER_LAUNCH_RESULT" in facts:
        dump("CX2H1B_PROVIDER_LAUNCH_RESULT.json", facts["CX2H1B_PROVIDER_LAUNCH_RESULT"])

    # Force journey classes per CX2H.1 scope
    tokens.J1_CLASS = "BLOCKED"
    tokens.J2_CLASS = "BLOCKED"
    tokens.J5_CLASS = "BLOCKED"
    tokens.J7_CLASS = "BLOCKED"
    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    tokens.J4_CLASS = "BLOCKED"
    tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE = False

    dump("CX2H_TOKENS.json", tokens.to_dict())
    gate = next_gate(tokens)
    report = {
        "schema": "gunnchos.cx2h.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX2H.1",
        "tokens": tokens.to_dict(),
        "firewall": {
            "device_lab_134_unaltered": tokens.CX2H_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX2H_PORTAL_14_UNALTERED and tokens.CX2H_PORTAL_15_UNALTERED,
            "device_lab_manifest_unaltered": tokens.CX2H_DEVICE_LAB_MANIFEST_UNALTERED,
            "evidence_path": "artifacts/complete_experience/cx2h",
            "no_merges": tokens.CX2H_NO_MERGES,
        },
        "NEXT_CX_GATE": gate,
        "lab_blocker": tokens.lab_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX2H_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX2H evidence\n\nPortal session + J3 App Center real-user lifecycle.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "J1/J2/J5/J7 remain BLOCKED in CX2H.1.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
