"""CX4 evidence writer."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx4.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx4.tokens import Cx4Tokens


def pick_next_gate(tokens: Cx4Tokens) -> str:
    if tokens.lab_blocker:
        return f"CX4_0B_{tokens.lab_blocker}"
    if tokens.CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS:
        return "CX4_OWNER_HUMAN_PHYSICAL_EXECUTION"
    for name in (
        "CURRENT_TIP_GUEST_OVERLAY_PASS",
        "CURRENT_TIP_GUEST_SMOKE_PASS",
        "HUMAN_A11Y_PACKET_READY",
        "PHYSICAL_PRINTER_PACKET_READY",
        "CAMERA_MIC_AV_PACKET_READY",
        "PHYSICAL_PERIPHERAL_PACKET_READY",
        "EVT_PACKET_READY",
        "DVT_PACKET_READY",
        "PVT_PACKET_READY",
        "FIRMWARE_LIFECYCLE_PACKET_READY",
        "SUPPORT_BUNDLE_READY",
        "REPAIR_RMA_PACKET_READY",
        "CHAT_MEETING_PROVIDER_READINESS_PASS",
        "EXTERNAL_ISSUER_PACKET_READY",
        "PRIVACY_REVIEW_PACKET_READY",
        "RIGHTS_REGISTER_READY",
        "CERTIFICATION_MATRIX_READY",
        "MANUFACTURING_PACKET_READY",
        "OWNER_ACTION_PACKET_READY",
    ):
        attr = f"CX4_{name}"
        if not getattr(tokens, attr, False):
            return f"CX4_0B_{name}"
    return "CX4_0B_UNKNOWN"


def write_evidence(repo: Optional[Path], tokens: Cx4Tokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    tokens.CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS = tokens.readiness_complete()
    tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE = False
    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    tokens.PHYSICAL_PRINTER_PENDING = True
    tokens.PHYSICAL_CAMERA_MIC_AV_PENDING = True
    tokens.EVT_PENDING = True
    tokens.DVT_PENDING = True
    tokens.PVT_PENDING = True
    tokens.human_a11y_pass = False
    tokens.physical_printer_pass = False
    tokens.physical_camera_mic_av_pass = False
    tokens.evt_pass = False
    tokens.dvt_pass = False
    tokens.pvt_pass = False
    tokens.certified = False
    tokens.certification_claimed = False
    tokens.legal_approval = False
    tokens.manufacturing_pass = False
    tokens.external_provider_integration_pass = False

    next_gate = pick_next_gate(tokens)
    report = {
        "schema": "gunnchos.cx4.evidence_report.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX4.0",
        "tokens": tokens.to_dict(),
        "facts": facts,
        "NEXT_CX_GATE": next_gate,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "firewall": {
            "CX4_DEVICE_LAB_134_UNALTERED": tokens.CX4_DEVICE_LAB_134_UNALTERED,
            "CX4_PORTAL_14_UNALTERED": tokens.CX4_PORTAL_14_UNALTERED,
            "CX4_PORTAL_15_UNALTERED": tokens.CX4_PORTAL_15_UNALTERED,
            "CX4_WAIKE_RELEASE_UNALTERED": tokens.CX4_WAIKE_RELEASE_UNALTERED,
            "CX4_NO_MERGES": tokens.CX4_NO_MERGES,
            "CX4_NO_DEVICE_LAB": tokens.CX4_NO_DEVICE_LAB,
        },
    }
    (ev / "CX4_0_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    (ev / "CX4_0_TOKENS.json").write_text(json.dumps(tokens.to_dict(), indent=2) + "\n")
    (ev / "README.md").write_text(
        "# CX4.0 evidence\n\nReadiness preparation only. Human/physical/external gates remain pending.\n"
        f"NEXT_CX_GATE={next_gate}\nFULL_COMPLETE_EXPERIENCE_COMPLETE=false\n"
    )
    return report
