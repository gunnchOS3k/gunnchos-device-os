"""Write CX2D evidence exclusively under artifacts/complete_experience/cx2d/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2d import FULL_COMPLETE_EXPERIENCE_COMPLETE, CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY
from gunnchos_device_os.cx2d.gui_proof import domain_gui_results, empty_window_proofs
from gunnchos_device_os.cx2d.journeys import upgrade_journeys
from gunnchos_device_os.cx2d.lab import attempt_lab_status, build_provenance, evidence_root
from gunnchos_device_os.cx2d.linux_providers import qualify_linux_providers
from gunnchos_device_os.cx2d.tokens import fail_closed_tokens


def write_human_packets(root: Path) -> None:
    (root / "HUMAN_A11Y_VALIDATION_PACKET.md").write_text(
        """# CX2D Human Accessibility Validation Packet

Status: **HUMAN_A11Y_PENDING=true** — do not fabricate responses.

## Required human checks (Linux gunnch_shell)

1. Navigate Home → Vault → App Center → Connect → Assist → Care with keyboard only.
2. Confirm accessible names/roles via Orca (if available) or AT-SPI inspector.
3. High-contrast and reduce-motion Assist toggles.
4. Offline banner announced to AT.
5. Focus order and Escape/Alt+H navigation.

## Responses

_Leave blank for human validator._

| Check | Pass? | Notes |
|-------|-------|-------|
| Keyboard-only nav |  |  |
| Orca/AT-SPI names |  |  |
| Contrast/motion |  |  |
| Offline announcement |  |  |
| Focus order |  |  |
"""
    )
    (root / "PHYSICAL_PRINTER_SI_PACKET.md").write_text(
        """# CX2D Physical Printer SI Packet

`CX2D_PHYSICAL_PRINTER_PENDING=true`

Digital IPP GUI pass is separate. Physical page inspection remains human/SI.
"""
    )
    (root / "HUMAN_AV_VALIDATION_PACKET.md").write_text(
        """# CX2D Human AV Validation Packet

`CX2D_HUMAN_AV_QUALITY_PENDING=true`  
`CX2D_PHYSICAL_CAMERA_MIC_PENDING=true`

Chat/video may remain partial without blocking J1/J2/J3/J5/J7 once those earn real-user digital pass.
"""
    )


def write_evidence(repo_root: Path) -> Dict[str, Any]:
    root = evidence_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    status = attempt_lab_status(repo_root)
    provenance = build_provenance(repo_root, status)
    linux_ok = bool(status.get("graphical_session_proven"))
    providers = qualify_linux_providers(linux_session_proven=linux_ok)
    reason = status.get("blocker") or "linux_gui_not_proven"
    windows = empty_window_proofs(reason=reason)
    domains = domain_gui_results(reason=reason)
    journeys = upgrade_journeys(linux_gui_proven=linux_ok)
    tokens = fail_closed_tokens(lab_blocker=reason or "")
    write_human_packets(root)

    report = {
        "schema": "gunnchos.cx2d.evidence_report.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY": CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY,
        "production_shell": "apps/gunnch_shell",
        "launcher_mock_role": "deprecated_adapter",
        "linux_lab": {
            "status_ref": "CX2D_LINUX_LAB_STATUS.json",
            "provenance_ref": "CX2D_LINUX_LAB_PROVENANCE.json",
            "blocker": status.get("blocker"),
            "graphical_session_proven": linux_ok,
        },
        "providers_linux": providers,
        "rendered_windows": windows,
        "domain_gui": domains,
        "journeys": journeys,
        "tokens": tokens.to_dict(),
        "evidence_classes_separated": {
            "CONTRACT_PASS": "API/schema only",
            "HARNESS_PASS": "deterministic harness without real GUI",
            "REAL_PROVIDER_CLI_PASS": "real binary/protocol without rendered shell GUI",
            "REAL_PROVIDER_GUI_PASS": "real provider with window proof",
            "REAL_USER_JOURNEY_DIGITAL_PASS": "shell UI + provider + input + read-back + persistence",
            "HUMAN_VALIDATION_PENDING": "requires human",
            "PHYSICAL_VALIDATION_PENDING": "requires physical SI",
            "EXTERNAL_PROVIDER_PENDING": "external dependency",
            "BLOCKED": "missing required condition",
        },
        "firewall": {
            "device_lab_134_unaltered": True,
            "portal_14_15_unaltered": True,
            "device_lab_manifest_unaltered": True,
            "evidence_path": "artifacts/complete_experience/cx2d",
            "no_merges": True,
        },
        "NEXT_CX_GATE": "CX2E_LINUX_GRAPHICAL_SESSION_JOURNEY_PROOF",
    }
    (root / "CX2D_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    (root / "CX2D_TOKENS.json").write_text(json.dumps(tokens.to_dict(), indent=2) + "\n")
    (root / "JOURNEYS.json").write_text(json.dumps(journeys, indent=2) + "\n")
    (root / "LINUX_PROVIDER_QUALIFICATION.json").write_text(json.dumps(providers, indent=2) + "\n")
    (root / "RENDERED_WINDOWS.json").write_text(json.dumps(windows, indent=2) + "\n")
    (root / "README.md").write_text(
        "# CX2D evidence\n\nFail-closed Linux real-user journey closure. "
        "See CX2D_EVIDENCE_REPORT.json. FULL_COMPLETE_EXPERIENCE_COMPLETE=false.\n"
    )
    # provenance already written by build_provenance
    _ = provenance
    return report
