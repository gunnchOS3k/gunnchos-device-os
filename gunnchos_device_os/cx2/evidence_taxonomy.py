"""Revised CX2 evidence hierarchy + CX1 honesty reclassification (additive)."""

from __future__ import annotations

from typing import Dict, List

EVIDENCE_CLASSES = (
    "CONTRACT_PASS",
    "HARNESS_PASS",
    "REAL_PROVIDER_CLI_PASS",
    "REAL_PROVIDER_GUI_PASS",
    "REAL_USER_JOURNEY_DIGITAL_PASS",
    "HUMAN_VALIDATION_PENDING",
    "PHYSICAL_VALIDATION_PENDING",
    "EXTERNAL_PROVIDER_PENDING",
    "NOT_APPLICABLE",
    # transitional honesty labels for partial real work
    "REAL_PROVIDER_PARTIAL",
    "HARNESS_ONLY",
    "BLOCKED",
)

# CX1 overstatements → honest CX2 class (does not rewrite CX1 artifact history)
CX1_RECLASSIFICATION: List[Dict[str, str]] = [
    {
        "cx1_claim": "App Center install via INSTALLED.json marker",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "marker_file_not_real_package_deploy",
    },
    {
        "cx1_claim": "App launch via LAST_LAUNCH.json",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "no_process_or_window_evidence",
    },
    {
        "cx1_claim": "Browser HTTPS via Python ssl.create_default_context",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "not_browser_tls_navigation",
    },
    {
        "cx1_claim": "Browser download via write_bytes fixture",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "not_browser_ui_download",
    },
    {
        "cx1_claim": "Upload file chooser via JSON adapter",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "not_real_portal_or_native_chooser",
    },
    {
        "cx1_claim": "PWA via manifest-only JSON",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "manifest_without_installable_runtime",
    },
    {
        "cx1_claim": "Writer edit via ODF byte append",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "not_odf_aware_edit_or_libreoffice_reopen",
    },
    {
        "cx1_claim": "Screenshot/screencast static fixture bytes",
        "cx1_class": "DIGITAL_PARTIAL",
        "cx2_class": "HARNESS_PASS",
        "reason": "fixture_not_compositor_capture",
    },
    {
        "cx1_claim": "Conference URL-to-JSON",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "no_webrtc_or_meeting_client",
    },
    {
        "cx1_claim": "CalDAV/CardDAV JSON store without protocol",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "json_fixture_not_caldav_carddav",
    },
    {
        "cx1_claim": "Virtual printer byte-copy output",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "not_cups_ipp_spool",
    },
    {
        "cx1_claim": "Assist a11y without rendered UI",
        "cx1_class": "DIGITAL_A11Y_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "semantics_model_not_rendered_ui",
    },
    {
        "cx1_claim": "LibreOffice headless convert create/export",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "REAL_PROVIDER_CLI_PASS",
        "reason": "real_soffice_process_when_binary_present",
    },
    {
        "cx1_claim": "Identity/Vault/Care harness contracts",
        "cx1_class": "DIGITAL_PASS",
        "cx2_class": "HARNESS_PASS",
        "reason": "valuable_harness_retained_not_real_gui_journey",
    },
]


def reclassification_document() -> dict:
    return {
        "schema": "gunnchos.cx2.evidence_reclassification.v1",
        "hierarchy": list(EVIDENCE_CLASSES),
        "policy": "downgrade_overstated_cx1_without_falsifying_cx1_history",
        "cx1_artifacts_retained": "artifacts/complete_experience/cx1/",
        "cx2_artifacts_root": "artifacts/complete_experience/cx2/",
        "reclassifications": CX1_RECLASSIFICATION,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
    }


def classify(*, real_gui: bool = False, real_provider_process: bool = False,
             real_protocol: bool = False, harness_only: bool = False,
             human_pending: bool = False, physical_pending: bool = False,
             external_pending: bool = False, blocked: bool = False,
             journey: bool = False) -> str:
    if blocked:
        return "BLOCKED"
    if physical_pending and not real_provider_process:
        return "PHYSICAL_VALIDATION_PENDING"
    if human_pending and not real_gui:
        return "HUMAN_VALIDATION_PENDING"
    if external_pending:
        return "EXTERNAL_PROVIDER_PENDING"
    if harness_only:
        return "HARNESS_PASS"
    if journey and real_gui and real_provider_process:
        return "REAL_USER_JOURNEY_DIGITAL_PASS"
    if real_gui and real_provider_process:
        return "REAL_PROVIDER_GUI_PASS"
    if real_provider_process or real_protocol:
        return "REAL_PROVIDER_CLI_PASS"
    if real_gui:
        return "HARNESS_PASS"
    return "HARNESS_ONLY"
