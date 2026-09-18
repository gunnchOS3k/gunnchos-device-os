"""Write CX2H.2 evidence under artifacts/complete_experience/cx2h2/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2h2 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2h2.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h2.tokens import Cx2h2Tokens


def next_gate(tokens: Cx2h2Tokens) -> str:
    if tokens.j1_digital_pass() and tokens.j7_digital_pass():
        return "CX2H3_BROWSER_MAIL_OFFLINE_J2_J5"
    if tokens.lab_blocker:
        frag = tokens.lab_blocker.split(":")[0].strip().replace(" ", "_")[:80]
        if frag.startswith("CX2H2_"):
            return "CX2H2B_" + frag[6:]
        if frag.startswith("CX2H_"):
            return "CX2H2B_" + frag[5:]
        return "CX2H2B_" + frag
    missing = []
    for name, ok in (
        ("WRITER_GUI", tokens.CX2H2_REAL_WRITER_GUI_PASS),
        ("VAULT_FILE", tokens.CX2H2_REAL_VAULT_FILE_PASS),
        ("PDF_EXPORT_GUI", tokens.CX2H2_REAL_PDF_EXPORT_GUI_PASS),
        ("IPP_PROVIDER", tokens.CX2H2_REAL_IPP_PROVIDER_PASS),
        ("IPP_PRINT_GUI", tokens.CX2H2_REAL_IPP_PRINT_GUI_PASS),
        ("BACKUP_GUI", tokens.CX2H2_REAL_BACKUP_GUI_PASS),
        ("RESTORE_GUI", tokens.CX2H2_REAL_RESTORE_GUI_PASS),
        ("PERSISTENCE", tokens.CX2H2_PERSISTENCE_PASS),
    ):
        if not ok:
            missing.append(name)
    if missing:
        return "CX2H2B_" + missing[0]
    if tokens.J1_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        return "CX2H2B_J1"
    if tokens.J7_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        return "CX2H2B_J7"
    return "CX2H3_BROWSER_MAIL_OFFLINE_J2_J5"


def write_evidence(repo: Optional[Path], tokens: Cx2h2Tokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    mirror = Path("/tmp/cx2h2_evidence")
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

    for key in (
        "CX2H2_WRITER_GUI_PROOF",
        "CX2H2_VAULT_FILE_PROVIDER_PROOF",
        "CX2H2_PDF_EXPORT_GUI_PROOF",
        "CX2H2_IPP_PRINTER_PROVENANCE",
        "CX2H2_PRINT_GUI_JOURNEY",
        "CX2H2_BACKUP_GUI_PROOF",
        "CX2H2_DESTRUCTIVE_EVENT",
        "CX2H2_RESTORE_GUI_PROOF",
        "CX2H2_PERSISTENCE_READBACK",
        "CX2H2_A11Y_NOTES",
        "CX2H2_SHELL_J3_PREREQ",
        "CX2H2_J1_JOURNEY",
        "CX2H2_J7_JOURNEY",
    ):
        if key in facts:
            dump(f"{key}.json", facts[key])

    # Force invariant classes
    tokens.J2_CLASS = "BLOCKED"
    tokens.J5_CLASS = "BLOCKED"
    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    tokens.J4_CLASS = "BLOCKED"
    tokens.CX2H2_PHYSICAL_PRINTER_PENDING = True
    tokens.CX2H_HUMAN_A11Y_PENDING = True
    tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE = False

    if tokens.j1_digital_pass():
        tokens.J1_CLASS = "REAL_USER_JOURNEY_DIGITAL_PASS"
    elif tokens.J1_CLASS not in ("REAL_USER_JOURNEY_DIGITAL_PASS", "REAL_PROVIDER_GUI_PARTIAL"):
        tokens.J1_CLASS = "REAL_PROVIDER_GUI_PARTIAL" if tokens.lab_blocker or any(
            [
                tokens.CX2H2_REAL_WRITER_GUI_PASS,
                tokens.CX2H2_REAL_VAULT_FILE_PASS,
                tokens.CX2H2_REAL_IPP_PROVIDER_PASS,
            ]
        ) else tokens.J1_CLASS

    if tokens.j7_digital_pass():
        tokens.J7_CLASS = "REAL_USER_JOURNEY_DIGITAL_PASS"
    elif tokens.J7_CLASS not in ("REAL_USER_JOURNEY_DIGITAL_PASS", "REAL_PROVIDER_GUI_PARTIAL"):
        tokens.J7_CLASS = "REAL_PROVIDER_GUI_PARTIAL" if (
            tokens.CX2H2_REAL_BACKUP_GUI_PASS or tokens.CX2H2_REAL_RESTORE_GUI_PASS
        ) else tokens.J7_CLASS

    dump("CX2H2_TOKENS.json", tokens.to_dict())
    gate = next_gate(tokens)
    report = {
        "schema": "gunnchos.cx2h2.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX2H.2",
        "tokens": tokens.to_dict(),
        "firewall": {
            "device_lab_134_unaltered": tokens.CX2H_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX2H_PORTAL_14_UNALTERED and tokens.CX2H_PORTAL_15_UNALTERED,
            "device_lab_manifest_unaltered": tokens.CX2H_DEVICE_LAB_MANIFEST_UNALTERED,
            "evidence_path": "artifacts/complete_experience/cx2h2",
            "no_merges": tokens.CX2H_NO_MERGES,
        },
        "NEXT_CX_GATE": gate,
        "lab_blocker": tokens.lab_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX2H2_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX2H.2 evidence\n\n"
        "Document/print/recovery journeys J1 + J7.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "J2/J5 BLOCKED; J6 HUMAN_VALIDATION_PENDING; PHYSICAL_PRINTER_PENDING=true.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
