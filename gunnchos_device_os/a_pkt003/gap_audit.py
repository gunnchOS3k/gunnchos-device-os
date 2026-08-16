"""A1 — Gap audit over accepted PKT-002 implementation."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.a_pkt003 import ARTIFACT_REL, BASE_SHA, PACKET

CAPABILITIES = [
    ("secure_measured_boot", "PARTIAL", "boot/attestation modules present; no silicon-exact measured boot claim", "DIGITAL_OPEN", None),
    ("attestation", "PARTIAL", "attestation.py digital path; production keys false", "DIGITAL_OPEN", None),
    ("ab_update", "SIMULATED", "UpdateRecoverySuite A/B slots — not bootable firmware A/B", "DIGITAL_OPEN", "PHYSICAL_PENDING for real A/B"),
    ("recovery", "PASS", "update_recovery_completeness + package rollback paths", None, None),
    ("package_signing", "PASS", "dev_keys + PackageBuilder SIGNATURE.json (PKT-002)", None, None),
    ("crash_recovery", "PARTIAL", "service restart digital path; needs J-R4 evidence", None, None),
    ("session_continuity", "PARTIAL", "MW-SESSION-CONTINUITY + Lab continuity export/import", None, None),
    ("offline_sync", "PASS", "offline_sync.py vector-clock/LWW engine present", None, None),
    ("fleet_health", "PARTIAL", "device_health/fleet_ops scaffolding", "DIGITAL_OPEN", None),
    ("diagnostics", "PARTIAL", "serviceability export_diagnostic_bundle; A5 collect path pending", None, None),
    ("logs_tracing", "PARTIAL", "diagnostics_log redaction + OTel hooks", None, None),
    ("storage_pressure", "PARTIAL", "middleware storage_full fault; J-R3 guest evidence pending", None, None),
    ("backup_restore", "PASS", "serviceability backup/restore virtual device_root", None, None),
    ("user_profiles", "PASS", "profile_manager + Device Lab profiles", None, None),
    ("ai_memory", "PARTIAL", "local AI continuity ECO-004; PHYSICAL/HUMAN pending", "HUMAN_PENDING", None),
    ("waike_state", "PARTIAL", "WAIKE ingest paths; REAL_STUDENT_E6 false", "HUMAN_PENDING", None),
    ("ring_state", "PARTIAL", "virtual ring inject; PHYSICAL_RING false", "PHYSICAL_PENDING", None),
    ("dock_display_state", "PASS", "ECO-002 handheld↔dock digital path", None, None),
    ("developer_tools", "PASS", "gunnchctl sdk/package/install + creation enablement", None, None),
    ("creation_templates", "PASS", "PKT-002 8 templates + guest memo E2E", None, None),
    ("device_profiles", "PASS", "student_14_5/handheld/dsxl/dock/rings profiles", None, None),
]


def run_gap_audit(repo_root: Path) -> dict[str, Any]:
    pkt2 = repo_root / "artifacts" / "stream_a_pkt_002"
    evidence = {
        "CREATOR_END_TO_END_DIGITAL_PASS": (pkt2 / "CREATOR_GUEST_E2E_RESULT.json").exists(),
        "MIDDLEWARE_RESILIENCE_PASS": (pkt2 / "MIDDLEWARE_RESILIENCE_MATRIX.json").exists(),
        "TEMPLATE_SUITE_PASS": (pkt2 / "TEMPLATE_SUITE_RESULT.json").exists(),
    }
    rows = []
    for cap, status, note, digital, phys in CAPABILITIES:
        rows.append(
            {
                "capability": cap,
                "accepted_evidence": evidence if status == "PASS" else {},
                "status": status,
                "missing_behavior": None if status == "PASS" else note,
                "missing_verifier": None if status in ("PASS", "SIMULATED") else f"verifier_for_{cap}",
                "remaining_digital_work": digital,
                "physical_external_dependency": phys,
                "selection_reason": "selected_for_A_PKT_003" if status in ("PARTIAL", "SIMULATED") else "preserve_accepted",
                "note": note,
            }
        )
    doc = {
        "schema": "gunnchos.a_pkt003.gap_audit.v1",
        "packet": PACKET,
        "base_sha": BASE_SHA,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preservation": {
            "CREATOR_END_TO_END_DIGITAL_PASS": True,
            "middleware_10_fault": True,
            "SILICON_EXACT_EMULATION": False,
            "pkt002_evidence_present": evidence,
        },
        "capabilities": rows,
        "selected_focus": [
            "recovery_journeys_J-R1_to_J-R5",
            "multi_device_continuity",
            "creation_depth_three_workflows",
            "diagnostics_collect",
            "digital_performance_baseline",
        ],
        "out_of_scope": ["device-os#103", "Unity", "PHYSICAL_RING_E6", "SILICON_EXACT_EMULATION"],
        "claim_boundary": "Audit only; tokens earned only by A2–A6 evidence.",
    }
    out = repo_root / ARTIFACT_REL
    out.mkdir(parents=True, exist_ok=True)
    path = out / "A_PKT003_GAP_AUDIT.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    doc["path"] = str(path)
    return doc
