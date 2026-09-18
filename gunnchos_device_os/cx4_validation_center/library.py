"""Accessible task library derived from CX4.0 readiness packs. Not all active by default."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.contracts import ValidationTask


def _task(**kwargs: Any) -> ValidationTask:
    return ValidationTask(**kwargs)


def build_task_library() -> List[ValidationTask]:
    """All executable CX4.0-derived templates. Sessions select packs; most inactive by default."""
    tasks: List[ValidationTask] = []

    tasks.append(
        _task(
            task_id="vc_human_a11y_primary",
            pack_id="human_a11y",
            title="Human accessibility session — primary surfaces",
            short_description="Run planned accessibility tasks across Home, Vault, App Center, and related surfaces.",
            purpose="Collect human accessibility observations for J6; software readiness alone is not a PASS.",
            evidence_class_target="HUMAN_OBSERVED",
            prerequisite_ids=["CX4_HUMAN_A11Y_PACKET_READY"],
            estimated_minutes=90,
            safety_notes=["Stop anytime", "Do not capture passwords or personal portfolio content"],
            participant_steps=[
                "Confirm consent on the consent screen",
                "Use only the assigned modality for this block",
                "Complete the primary task on the assigned surface",
                "Trigger one recoverable error and recover",
                "Rate the task and add comments",
            ],
            moderator_steps=[
                "Record environment (device, SR version, zoom)",
                "Observe without coaching unless safety requires it",
                "File severity-1 issues immediately",
            ],
            expected_result="Observation form complete with evidence attachments for assigned surfaces.",
            pass_rule="Real participant sessions; required evidence; severity1_open==0; reviewer signoff; attestation.",
            required_evidence=["observation_form", "screenshot_or_log"],
            optional_evidence=["screen_recording"],
            issue_categories=["focus", "name_role", "contrast", "keyboard_trap", "sr_silence", "other"],
            device_or_sku="Student 14.5 / any shell surface",
            requires_human=True,
            requires_physical=False,
            status="available",
            edmund_action_id="1",
            gate_unlocked="human_a11y_pass / J6_CLASS upgrade",
            required_equipment=["participant", "moderator", "optional screen reader"],
            active_by_default=False,
        )
    )

    tasks.append(
        _task(
            task_id="vc_physical_printer",
            pack_id="physical_printer",
            title="Physical printer validation",
            short_description="Connect a named USB and/or LAN printer and complete the printer packet.",
            purpose="Clear PHYSICAL_PRINTER_PENDING only with real hardware evidence.",
            evidence_class_target="HUMAN_OBSERVED+SYSTEM_CAPTURED",
            prerequisite_ids=["CX4_PHYSICAL_PRINTER_PACKET_READY"],
            estimated_minutes=120,
            safety_notes=["Use only approved printers", "Do not force paper jams"],
            participant_steps=[
                "Confirm printer is connected and powered",
                "Print the test page from Writer or Care",
                "Photograph output if consented",
                "Confirm job ID appears in system collector (or moderator attaches mock for UI drills only)",
            ],
            moderator_steps=["Run CUPS collector", "Record printer model and connection path", "Attach output photos"],
            expected_result="Successful USB or LAN print with job IDs and output integrity evidence.",
            pass_rule="Real printer path + collector bundle + reviewer signoff.",
            required_evidence=["cups_collector_bundle", "output_photo_or_hash"],
            optional_evidence=["lan_discovery_log"],
            issue_categories=["discovery", "job_failure", "output_quality", "other"],
            device_or_sku="Student 14.5 / Docked",
            requires_human=True,
            requires_physical=True,
            status="available",
            edmund_action_id="2",
            gate_unlocked="PHYSICAL_PRINTER_PENDING clearance",
            required_equipment=["named USB or LAN printer"],
            active_by_default=False,
        )
    )

    tasks.append(
        _task(
            task_id="vc_camera_mic_av",
            pack_id="camera_mic_av",
            title="Camera / microphone / AV validation",
            short_description="Exercise camera, mic, and AV permission flows on physical devices.",
            purpose="Clear PHYSICAL_CAMERA_MIC_AV_PENDING with field evidence.",
            evidence_class_target="HUMAN_OBSERVED+SYSTEM_CAPTURED",
            prerequisite_ids=["CX4_CAMERA_MIC_AV_PACKET_READY"],
            estimated_minutes=120,
            safety_notes=["Respect media consent", "No recording of bystanders without consent"],
            participant_steps=[
                "Grant or deny camera permission as instructed",
                "Capture a short test clip only if media consent was accepted",
                "Speak a test phrase into the mic",
                "Note quality and permission UX",
            ],
            moderator_steps=["Run AV diagnostics collector", "Record device names", "File privacy issues"],
            expected_result="AV checklist complete with diagnostics and human quality notes.",
            pass_rule="Field checklist complete; no severity-1 privacy failures; reviewer signoff.",
            required_evidence=["av_diagnostics", "quality_notes"],
            optional_evidence=["short_clip"],
            issue_categories=["permission", "quality", "privacy", "other"],
            device_or_sku="Student 14.5 / Handheld Hybrid",
            requires_human=True,
            requires_physical=True,
            status="available",
            edmund_action_id="3",
            gate_unlocked="PHYSICAL_CAMERA_MIC_AV_PENDING clearance",
            required_equipment=["physical camera/mic"],
            active_by_default=False,
        )
    )

    tasks.append(
        _task(
            task_id="vc_physical_peripherals",
            pack_id="physical_peripherals",
            title="Physical peripheral matrix",
            short_description="Validate keyboard, mouse, touch, BT, dock, and Ring as available.",
            purpose="Prove peripheral matrix on real devices.",
            evidence_class_target="HUMAN_OBSERVED+SYSTEM_CAPTURED",
            prerequisite_ids=["CX4_PHYSICAL_PERIPHERAL_PACKET_READY"],
            estimated_minutes=150,
            safety_notes=["Hot-plug carefully", "Do not force connectors"],
            participant_steps=[
                "Connect the assigned peripheral",
                "Complete a primary interaction",
                "Disconnect and reconnect once",
                "Note any lag or dropouts",
            ],
            moderator_steps=["Run peripheral collector", "Log reconnect mutations"],
            expected_result="Per-device checks recorded with enumeration and reconnect logs.",
            pass_rule="Named peripherals checked on real hardware; reviewer signoff.",
            required_evidence=["peripheral_matrix_log"],
            optional_evidence=["photo_of_setup"],
            issue_categories=["enumeration", "reconnect", "latency", "other"],
            device_or_sku="Device Quartet + Dock + Rings",
            requires_human=True,
            requires_physical=True,
            status="available",
            edmund_action_id="4",
            gate_unlocked="physical_peripheral_pass",
            required_equipment=["named peripherals"],
            active_by_default=False,
        )
    )

    skus = [
        ("student_14_5", "Student 14.5"),
        ("handheld_hybrid", "Handheld Hybrid"),
        ("ds_xl_coder", "DS-XL Coder"),
        ("edge_io_rings", "Edge I/O Rings"),
        ("first_party_dock", "First-party Dock"),
    ]
    for stage, stage_token, edmund in (
        ("evt", "EVT_PENDING", "5"),
        ("dvt", "DVT_PENDING", "5"),
        ("pvt", "PVT_PENDING", "5"),
    ):
        for sku_id, sku_name in skus:
            tasks.append(
                _task(
                    task_id=f"vc_{stage}_{sku_id}",
                    pack_id=f"device_quartet_{stage}",
                    title=f"{sku_name} {stage.upper()} validation",
                    short_description=f"Execute the {stage.upper()} packet for {sku_name}.",
                    purpose=f"Clear {stage_token} only with real hardware stage evidence.",
                    evidence_class_target="HUMAN_OBSERVED",
                    prerequisite_ids=[f"CX4_{stage.upper()}_PACKET_READY"],
                    estimated_minutes=240 if stage == "evt" else 480,
                    safety_notes=["Do not fabricate hardware", "Follow lab ESD rules"],
                    participant_steps=[
                        "Confirm board/SKU identity",
                        "Follow the stage packet checklist",
                        "Record failures with severity",
                        "Attach stage report evidence",
                    ],
                    moderator_steps=["Verify hardware identity", "Store stage report under evidence store"],
                    expected_result=f"{stage.upper()} report for {sku_name}.",
                    pass_rule=f"{stage.upper()} gates green per SKU packet + reviewer signoff.",
                    required_evidence=[f"{stage}_report"],
                    optional_evidence=["thermal_log", "photo"],
                    issue_categories=["bringup", "thermal", "mechanical", "wireless", "other"],
                    device_or_sku=sku_name,
                    requires_human=True,
                    requires_physical=True,
                    status="pending_external" if stage != "evt" else "available",
                    edmund_action_id=edmund,
                    gate_unlocked=f"{stage_token} clearance",
                    required_equipment=[f"{stage.upper()} hardware for {sku_name}"],
                    active_by_default=False,
                )
            )

    tasks.append(
        _task(
            task_id="vc_firmware_lifecycle",
            pack_id="firmware_lifecycle",
            title="Firmware lifecycle field check",
            short_description="Run firmware inventory and failed-update recovery on real devices (simulation ≠ PASS).",
            purpose="Collect field firmware evidence; simulation harness remains distinct.",
            evidence_class_target="SYSTEM_CAPTURED+HUMAN_OBSERVED",
            prerequisite_ids=["CX4_FIRMWARE_LIFECYCLE_PACKET_READY"],
            estimated_minutes=90,
            safety_notes=["Do not brick devices", "Keep recovery media ready"],
            participant_steps=["Confirm current firmware version", "Attempt approved update path", "Verify recovery path if instructed"],
            moderator_steps=["Capture firmware inventory", "Distinguish sim vs physical"],
            expected_result="Firmware inventory + recovery notes with clear sim vs physical labeling.",
            pass_rule="Physical device evidence only; simulation never sets physical_pass.",
            required_evidence=["firmware_inventory"],
            optional_evidence=["recovery_log"],
            issue_categories=["update_fail", "recovery", "other"],
            device_or_sku="any",
            requires_human=True,
            requires_physical=True,
            status="available",
            edmund_action_id=None,
            gate_unlocked=None,
            required_equipment=["target device"],
            active_by_default=False,
        )
    )

    tasks.append(
        _task(
            task_id="vc_support_care_rma",
            pack_id="support_repair_rma",
            title="Support / Care / repair / RMA walkthrough",
            short_description="Exercise support bundle and repair intake templates with a facilitator.",
            purpose="Validate support/repair readiness packets with human operators.",
            evidence_class_target="HUMAN_OBSERVED",
            prerequisite_ids=["CX4_SUPPORT_BUNDLE_READY", "CX4_REPAIR_RMA_PACKET_READY"],
            estimated_minutes=60,
            safety_notes=["Do not include real customer PII in drills"],
            participant_steps=["Open Care", "Generate a support bundle (or attach mock)", "Complete repair intake draft"],
            moderator_steps=["Redact PII", "Confirm bundle hashes"],
            expected_result="Support bundle + intake draft stored locally.",
            pass_rule="Operator completes intake; reviewer signoff; no PII leakage.",
            required_evidence=["support_bundle_or_intake"],
            optional_evidence=["screenshot"],
            issue_categories=["intake", "bundle", "privacy", "other"],
            device_or_sku="any",
            requires_human=True,
            status="available",
            active_by_default=False,
        )
    )

    tasks.append(
        _task(
            task_id="vc_external_chat_meeting",
            pack_id="external_chat_meeting",
            title="External chat / meeting provider validation",
            short_description="Live validation against provider contracts when credentials exist.",
            purpose="Collect external provider integration evidence without claiming PASS from contracts alone.",
            evidence_class_target="HUMAN_OBSERVED",
            prerequisite_ids=["CX4_CHAT_MEETING_PROVIDER_READINESS_PASS"],
            estimated_minutes=120,
            safety_notes=["Use approved test accounts only"],
            participant_steps=["Join test meeting", "Send test chat", "Verify AV permissions"],
            moderator_steps=["Capture live traces", "Do not store credentials in evidence"],
            expected_result="Live traces attached; credentials never stored.",
            pass_rule="Live provider session + reviewer signoff.",
            required_evidence=["live_trace_notes"],
            optional_evidence=["screenshot"],
            issue_categories=["auth", "av", "chat", "other"],
            device_or_sku="any",
            requires_human=True,
            requires_external_provider=True,
            status="pending_external",
            edmund_action_id="6",
            gate_unlocked="external_provider_integration evidence",
            required_equipment=["provider credentials"],
            active_by_default=False,
        )
    )

    tasks.append(
        _task(
            task_id="vc_institutional_issuer",
            pack_id="institutional_issuer",
            title="Institutional issuer onboarding checks",
            short_description="Human review checklist for issuer onboarding engagement.",
            purpose="Track issuer engagement; certification_claimed stays false unless earned.",
            evidence_class_target="HUMAN_OBSERVED",
            prerequisite_ids=["CX4_EXTERNAL_ISSUER_PACKET_READY"],
            estimated_minutes=180,
            safety_notes=["Do not claim certification from checklist alone"],
            participant_steps=["Review onboarding packet", "Record issuer contact outcome", "Attach trust-exchange notes if any"],
            moderator_steps=["Keep certification_claimed=false unless earned"],
            expected_result="Onboarding checklist progress recorded.",
            pass_rule="Real issuer engagement evidence + reviewer signoff; no auto-certify.",
            required_evidence=["issuer_checklist_notes"],
            optional_evidence=["email_redacted"],
            issue_categories=["trust", "revocation", "other"],
            device_or_sku="n/a",
            requires_human=True,
            requires_external_provider=True,
            status="pending_external",
            edmund_action_id="7",
            gate_unlocked="external issuer evidence",
            required_equipment=["willing issuer org"],
            active_by_default=False,
        )
    )

    for tid, pack, title, prereq, edmund, gate in (
        (
            "vc_privacy_review",
            "privacy_review",
            "Privacy review checklist",
            "CX4_PRIVACY_REVIEW_PACKET_READY",
            "8",
            "legal_approval",
        ),
        (
            "vc_rights_review",
            "rights_review",
            "Rights review checklist",
            "CX4_RIGHTS_REGISTER_READY",
            "8",
            "legal_approval",
        ),
        (
            "vc_certification_evidence",
            "certification",
            "Certification evidence collection",
            "CX4_CERTIFICATION_MATRIX_READY",
            "9",
            "certified",
        ),
        (
            "vc_manufacturing_evidence",
            "manufacturing",
            "Manufacturing evidence collection",
            "CX4_MANUFACTURING_PACKET_READY",
            None,
            "manufacturing_pass",
        ),
    ):
        tasks.append(
            _task(
                task_id=tid,
                pack_id=pack,
                title=title,
                short_description=f"Human checklist for {title.lower()} (preparation ≠ approval).",
                purpose="Collect review evidence; never auto-set legal/cert/mfg PASS.",
                evidence_class_target="HUMAN_OBSERVED",
                prerequisite_ids=[prereq],
                estimated_minutes=120,
                safety_notes=["Counsel/lab conclusions only from signed review", "Matrix alone never certifies"],
                participant_steps=["Open checklist", "Mark each row with notes", "Attach supporting docs if any"],
                moderator_steps=["Ensure legal_approval/certified/manufacturing_pass remain false without signed evidence"],
                expected_result="Checklist progress with attachments.",
                pass_rule="Signed review/lab evidence + reviewer signoff; never from packet alone.",
                required_evidence=["checklist_notes"],
                optional_evidence=["signed_memo"],
                issue_categories=["gap", "risk", "other"],
                device_or_sku="n/a",
                requires_human=True,
                requires_external_provider=pack in {"certification", "manufacturing"},
                status="pending_external" if pack in {"certification", "manufacturing", "privacy_review", "rights_review"} else "available",
                edmund_action_id=edmund,
                gate_unlocked=gate,
                required_equipment=["counsel or lab" if pack != "manufacturing" else "mfg partner"],
                active_by_default=False,
            )
        )

    # Soft default pack for software drills (does not unlock human gates)
    tasks.append(
        _task(
            task_id="vc_software_smoke_walkthrough",
            pack_id="validation_center_smoke",
            title="Validation Center software walkthrough (non-gate)",
            short_description="Exercise UI flows without claiming human/physical PASS.",
            purpose="Qualify Validation Center software only.",
            evidence_class_target="HUMAN_OBSERVED",
            prerequisite_ids=[],
            estimated_minutes=15,
            safety_notes=["This walkthrough never promotes human/physical gates"],
            participant_steps=[
                "Accept consent",
                "Start the task",
                "Mark steps complete",
                "Attach a text note as evidence",
                "Complete ratings",
                "Submit task",
            ],
            moderator_steps=["Confirm no gate tokens flip"],
            expected_result="Session can be submitted for software QA only.",
            pass_rule="N/A — software qualification only; does not unlock product gates.",
            required_evidence=["text_note"],
            optional_evidence=[],
            issue_categories=["ui", "other"],
            device_or_sku="host",
            requires_human=True,
            requires_physical=False,
            status="available",
            active_by_default=True,
            gate_unlocked=None,
        )
    )

    return tasks


def packs_summary(tasks: Optional[List[ValidationTask]] = None) -> List[Dict[str, Any]]:
    tasks = tasks or build_task_library()
    packs: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        p = packs.setdefault(
            t.pack_id,
            {
                "pack_id": t.pack_id,
                "task_count": 0,
                "active_by_default_count": 0,
                "requires_physical": False,
                "requires_external_provider": False,
                "status": "available",
                "task_ids": [],
            },
        )
        p["task_count"] += 1
        p["task_ids"].append(t.task_id)
        if t.active_by_default:
            p["active_by_default_count"] += 1
        p["requires_physical"] = p["requires_physical"] or t.requires_physical
        p["requires_external_provider"] = p["requires_external_provider"] or t.requires_external_provider
        if t.status == "pending_external":
            p["status"] = "pending_external"
    return list(packs.values())


def get_task(task_id: str) -> Optional[ValidationTask]:
    for t in build_task_library():
        if t.task_id == task_id:
            return t
    return None


def tasks_for_packs(pack_ids: List[str], *, only_active_default: bool = False) -> List[ValidationTask]:
    out = []
    for t in build_task_library():
        if t.pack_id in pack_ids:
            if only_active_default and not t.active_by_default:
                continue
            out.append(t)
    return out


def default_selected_task_ids(pack_ids: List[str]) -> List[str]:
    """Select only active-by-default tasks within chosen packs (usually smoke)."""
    return [t.task_id for t in tasks_for_packs(pack_ids) if t.active_by_default]
