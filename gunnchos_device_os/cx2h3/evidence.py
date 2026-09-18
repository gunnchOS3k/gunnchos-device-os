"""Write CX2H.3 evidence under artifacts/complete_experience/cx2h3/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2h3 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2h3.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h3.tokens import Cx2h3Tokens


def next_gate(tokens: Cx2h3Tokens) -> str:
    if tokens.j2_digital_pass() and tokens.j5_digital_pass():
        return "CX2H4_P0_DIGITAL_CLOSURE_AUDIT"
    if tokens.lab_blocker:
        frag = tokens.lab_blocker.split(":")[0].strip().replace(" ", "_")[:80]
        if frag.startswith("CX2H3_"):
            return "CX2H3B_" + frag[6:]
        if frag.startswith("CX2H2_"):
            return "CX2H3B_" + frag[6:]
        if frag.startswith("CX2H_"):
            return "CX2H3B_" + frag[5:]
        return "CX2H3B_" + frag
    checks = (
        ("PREREQUISITE", tokens.CX2H3_PREREQUISITE_PASS),
        ("HTTPS_PROVIDER", tokens.CX2H3_REAL_HTTPS_PROVIDER_PASS),
        ("BROWSER_GUI", tokens.CX2H3_REAL_BROWSER_GUI_PASS),
        ("HTTPS_DOWNLOAD_GUI", tokens.CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS),
        ("DOCUMENT_EDIT", tokens.CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS),
        ("SMTP_IMAP_PROVIDER", tokens.CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS),
        ("MAIL_GUI", tokens.CX2H3_REAL_MAIL_GUI_PASS),
        ("MAIL_ATTACHMENT_ROUNDTRIP", tokens.CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS),
        ("J2_PERSISTENCE", tokens.CX2H3_J2_PERSISTENCE_PASS),
        ("OFFLINE_LOCAL_WORK", tokens.CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS),
        ("OFFLINE_MAIL_QUEUE", tokens.CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS),
        ("OFFLINE_RESTART", tokens.CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS),
        ("EXACTLY_ONCE", tokens.CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS),
        ("RECONNECT_FAILURE_RECOVERY", tokens.CX2H3_RECONNECT_FAILURE_RECOVERY_PASS),
    )
    for name, ok in checks:
        if not ok:
            return "CX2H3B_" + name
    if tokens.J2_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        return "CX2H3B_J2"
    if tokens.J5_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        return "CX2H3B_J5"
    return "CX2H4_P0_DIGITAL_CLOSURE_AUDIT"


def write_evidence(repo: Optional[Path], tokens: Cx2h3Tokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    mirror = Path("/tmp/cx2h3_evidence")
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

    for key, obj in facts.items():
        if key.startswith("CX2H3_") and isinstance(obj, (dict, list)):
            dump(f"{key}.json", obj)

    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    tokens.J4_CLASS = "BLOCKED"
    tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE = False

    if tokens.j2_digital_pass():
        tokens.J2_CLASS = "REAL_USER_JOURNEY_DIGITAL_PASS"
    elif tokens.J2_CLASS not in ("REAL_USER_JOURNEY_DIGITAL_PASS", "REAL_PROVIDER_GUI_PARTIAL"):
        tokens.J2_CLASS = "REAL_PROVIDER_GUI_PARTIAL"

    if tokens.j5_digital_pass():
        tokens.J5_CLASS = "REAL_USER_JOURNEY_DIGITAL_PASS"
    elif tokens.J2_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        tokens.J5_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        if not tokens.lab_blocker:
            tokens.lab_blocker = "CX2H3_J5_REQUIRES_J2_PASS"
    elif tokens.J5_CLASS not in ("REAL_USER_JOURNEY_DIGITAL_PASS", "REAL_PROVIDER_GUI_PARTIAL"):
        tokens.J5_CLASS = "REAL_PROVIDER_GUI_PARTIAL"

    dump("CX2H3_TOKENS.json", tokens.to_dict())
    gate = next_gate(tokens)
    report = {
        "schema": "gunnchos.cx2h3.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "wave": "CX2H.3",
        "tokens": tokens.to_dict(),
        "firewall": {
            "device_lab_134_unaltered": tokens.CX2H_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX2H_PORTAL_14_UNALTERED and tokens.CX2H_PORTAL_15_UNALTERED,
            "device_lab_manifest_unaltered": tokens.CX2H_DEVICE_LAB_MANIFEST_UNALTERED,
            "evidence_path": "artifacts/complete_experience/cx2h3",
            "lab_path": "os_build/cx2h3_linux_lab",
            "no_merges": tokens.CX2H_NO_MERGES,
        },
        "NEXT_CX_GATE": gate,
        "lab_blocker": tokens.lab_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX2H3_EVIDENCE_REPORT.json", report)
    readme = (
        "# CX2H.3 evidence\n\n"
        "Browser + mail + offline/reconnect journeys J2 + J5.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
        "J6 HUMAN_VALIDATION_PENDING.\n"
    )
    for d in (root, mirror):
        try:
            (d / "README.md").write_text(readme)
        except OSError:
            continue
    return report
