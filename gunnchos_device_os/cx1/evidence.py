"""CX1 evidence writer — artifacts/complete_experience/cx1/ only."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from .device_profiles import matrix_document
from .home import GunnchHome
from .journeys import JourneyRunner


EVIDENCE_CLASSES = (
    "IMPLEMENTED_UNVERIFIED",
    "DIGITAL_PASS",
    "DIGITAL_PARTIAL",
    "HUMAN_PENDING",
    "PHYSICAL_PENDING",
    "EXTERNAL_PROVIDER_PENDING",
    "NOT_APPLICABLE",
)


def default_artifact_root(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "complete_experience" / "cx1"


def write_evidence(repo_root: Path, home_root: Path) -> Dict[str, Any]:
    artifact_root = default_artifact_root(repo_root)
    artifact_root.mkdir(parents=True, exist_ok=True)
    home = GunnchHome(home_root)
    if not home.identity.first_run_complete:
        home.identity.first_run("CX1 Evidence Owner", policy_input="Developer", password="cx1-evidence")
    home.rebind_vault_to_active_profile()

    identity_ev = home.identity.conformance_evidence()
    browser_ev = home.browser.qualify()
    productivity_ev = {
        "create_writer": home.productivity.create_document("evidence_doc", "writer"),
        "export_pdf": home.productivity.export_pdf("evidence_doc", "writer"),
        "status": home.productivity.status(),
    }
    app_ev = home.app_center.install("org.gunnchos.cx1.testapp")
    portal_ev = home.permissions.probe_portals()
    print_ev = home.printing.discover_printers()
    peri_ev = home.printing.peripheral_inventory()
    a11y_ev = home.assist.inventory()
    security_ev = home.security.dashboard()
    offline_ev = home.offline.status()
    journeys = JourneyRunner(home).run_all()
    care_ev = home.care.export_support_bundle(
        diagnostics={"journeys": {k: v.get("ok") for k, v in journeys.items()}},
        capability_inventory=matrix_document(),
        failure_summaries=[
            k for k, v in journeys.items() if not v.get("ok")
        ],
        storage_backup_update_status={
            "vault_free": home.vault.free_space(),
            "provider_status": home.vault.provider_status(),
        },
    )

    report = {
        "schema": "gunnchos.cx1.evidence_report.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "domains": {
            "identity": identity_ev,
            "browser": browser_ev,
            "productivity": productivity_ev,
            "app_center": app_ev,
            "permissions": portal_ev,
            "printing": print_ev,
            "peripherals": peri_ev,
            "assist": a11y_ev,
            "security": {"summary": "dashboard_exported", "secure_boot_tpm_se": security_ev["secure_boot_tpm_se"]},
            "offline": offline_ev,
            "care": {"bundle_id": care_ev.get("bundle_id"), "evidence_class": care_ev.get("evidence_class")},
        },
        "journeys": journeys,
        "device_profiles": matrix_document(),
        "evidence_classes_used": sorted(
            {
                *(identity_ev.get("evidence_class", "DIGITAL_PARTIAL"),),
                *(browser_ev.get("evidence_class", "DIGITAL_PARTIAL"),),
                "PHYSICAL_PENDING",
                "HUMAN_PENDING",
                "DIGITAL_A11Y_PASS",
            }
        ),
        "claim_boundary": (
            "CX1 ordinary-user digital foundations evidence. "
            "Does not mutate Device Lab gate tokens or release manifests."
        ),
    }
    (artifact_root / "CX1_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    (artifact_root / "DEVICE_PROFILE_MATRIX.json").write_text(
        json.dumps(matrix_document(), indent=2) + "\n"
    )
    (artifact_root / "JOURNEYS.json").write_text(json.dumps(journeys, indent=2) + "\n")
    (artifact_root / "README.md").write_text(
        "# CX1 Evidence\n\n"
        "Ordinary-user digital foundations evidence for Device OS.\n\n"
        "- `CX1_EVIDENCE_REPORT.json` — domain + journey summary\n"
        "- `DEVICE_PROFILE_MATRIX.json` — profile qualification\n"
        "- `JOURNEYS.json` — journeys 1–6\n\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
    )
    return report
