"""CX2 evidence writer — artifacts/complete_experience/cx2/ only."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2.evidence_taxonomy import reclassification_document
from gunnchos_device_os.cx2.journeys import AuthenticJourneyRunner
from gunnchos_device_os.cx2.profiles import matrix_document
from gunnchos_device_os.cx2.shell.product_shell import ProductShell


def default_artifact_root(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "complete_experience" / "cx2"


def write_evidence(repo_root: Path, home_root: Path) -> Dict[str, Any]:
    artifact_root = default_artifact_root(repo_root)
    artifact_root.mkdir(parents=True, exist_ok=True)
    shell = ProductShell(home_root)
    shell.ensure_first_run("CX2 Evidence Owner", "Developer")
    reg = shell.provider_registry()

    browser = reg.browser.qualify(allow_gui=False)
    productivity = {
        "create": reg.productivity.create_document("evidence_doc", "writer", body="CX2 evidence"),
        "edit": reg.productivity.edit_via_libreoffice("evidence_doc", "writer", append=" v2"),
        "pdf": reg.productivity.export_pdf("evidence_doc", "writer"),
        "status": reg.productivity.status(),
    }
    apps = {
        "install": reg.app_center.install("org.gunnchos.cx2.testapp", "1.0.0"),
        "launch": reg.app_center.launch("org.gunnchos.cx2.testapp"),
        "update": reg.app_center.update("org.gunnchos.cx2.testapp", "2.0.0"),
        "uninstall": reg.app_center.uninstall("org.gunnchos.cx2.testapp"),
        "info": reg.app_center.provider_info(),
    }
    connect = reg.connect
    connect.start_local_stack()
    try:
        mail = connect.compose_send_receive()
        cal = connect.calendar_crud()
        contacts = connect.contacts_crud()
        chat = connect.status_chat_video()
    finally:
        connect.stop()
    capture = {
        "screenshot": reg.capture.screenshot_to_vault("evidence"),
        "screencast": reg.capture.screencast_to_vault("evidence"),
    }
    printing = reg.printing.discover()
    portals = reg.portals.probe()
    journeys = AuthenticJourneyRunner(shell).run_all()
    surfaces = {sid: shell.surface(sid).get("title") for sid in ("home", "vault", "app_center", "connect", "assist", "care")}
    restart = shell.restart_return_home()

    report = {
        "schema": "gunnchos.cx2.evidence_report.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "surfaces": surfaces,
        "restart_home": restart,
        "domains": {
            "browser": browser,
            "productivity": productivity,
            "app_center": apps,
            "connect": {"mail": mail, "calendar": cal, "contacts": contacts, "chat_video": chat},
            "capture": capture,
            "printing": printing,
            "portals": portals,
            "assist": shell.assist_model(),
            "care": shell.care_model(),
        },
        "journeys": journeys,
        "device_profiles": matrix_document(),
        "cx1_reclassification": reclassification_document(),
        "claim_boundary": (
            "CX2 evidence under artifacts/complete_experience/cx2/. "
            "Does not mutate Device Lab gate tokens, #134, Portal #14/#15, or WAIKE/gunnchAI."
        ),
    }
    (artifact_root / "CX2_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    (artifact_root / "CX1_RECLASSIFICATION.json").write_text(
        json.dumps(reclassification_document(), indent=2) + "\n"
    )
    (artifact_root / "DEVICE_PROFILE_MATRIX.json").write_text(json.dumps(matrix_document(), indent=2) + "\n")
    (artifact_root / "JOURNEYS.json").write_text(json.dumps(journeys, indent=2) + "\n")
    (artifact_root / "PRODUCT_PROVIDER_MATRIX.json").write_text(
        json.dumps(
            {
                "schema": "gunnchos.cx2.product_vs_provider.v1",
                "product_surfaces": {
                    "Home": True,
                    "Vault": True,
                    "AppCenter": True,
                    "Connect": True,
                    "Assist": True,
                    "Care": True,
                },
                "providers": {
                    "local_package_repo": True,
                    "flatpak": bool(reg.app_center.flatpak),
                    "browser": browser.get("browser_name"),
                    "libreoffice": productivity["status"]["libreoffice_available"],
                    "cups": printing.get("cups_client"),
                    "xdg_portal": portals.get("portal_bus_available"),
                },
            },
            indent=2,
        )
        + "\n"
    )
    (artifact_root / "README.md").write_text(
        "# CX2 Evidence\n\nReal-surface + provider productization evidence. "
        "Separate from Device Lab artifacts.\n\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
    )
    (artifact_root / "HUMAN_A11Y_VALIDATION_PACKET.md").write_text(
        """# Human Accessibility Validation Packet (CX2)

HUMAN_A11Y_PENDING=true / HUMAN_VALIDATION_PENDING=true

## Checklist (human operator)

1. Keyboard-only traverse Home → Vault → App Center → Connect → Assist → Care
2. Focus ring visible on every control; tab order matches nav model
3. Screen reader (Orca/VoiceOver) announces accessible names/roles
4. Zoom 200% without clipping critical controls
5. High contrast + reduced motion settings apply in rendered UI
6. No keyboard traps in modals (install progress, compose, restore)
7. Touch targets ≥44px on Handheld / Student profiles

Record PASS/FAIL per item with date, profile, AT version. Do not auto-PASS from CI.
"""
    )
    (artifact_root / "PHYSICAL_PRINTER_SI_PACKET.md").write_text(
        """# Physical Printer SI Packet

PHYSICAL_PRINTER_VALIDATION_PENDING=true

- USB IPP discovery
- LAN IPP Everywhere
- Duplex / color / paper size
- Cancel mid-job
- Scanner/MFP path if present
- Output integrity vs digital PDF
"""
    )
    return report
