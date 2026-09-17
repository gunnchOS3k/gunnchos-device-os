"""Master non-digital blocker register + Edmund action packet (prep only)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4.paths import evidence_root, readiness_docs_root, repo_root_from_here


def build_blocker_register() -> Dict[str, Any]:
    blockers: List[Dict[str, Any]] = [
        {
            "blocker_id": "CX4-H-J6-A11Y",
            "class": "Human",
            "exact_requirement": "Human accessibility validation across primary surfaces",
            "affected_product_sku": "All first-party shell surfaces",
            "prerequisite": "CX4_HUMAN_A11Y_PACKET_READY",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Run HUMAN_A11Y_VALIDATION_PACKET with planned participants",
            "person_org_needed": "Edmund + a11y facilitator + participants",
            "evidence_required": "Observation forms + issues + evidence uploads",
            "pass_rule": "planned participants complete; severity1_open==0; attestation",
            "estimated_field_session_duration": "estimate 6-8 hours total (plan, not evidence)",
            "status": "PENDING_HUMAN",
            "token_unlocked": "human_a11y_pass / J6_CLASS upgrade",
        },
        {
            "blocker_id": "CX4-P-PRINTER",
            "class": "Physical",
            "exact_requirement": "USB and/or LAN IPP Everywhere physical print validation",
            "affected_product_sku": "Student 14.5 / Docked",
            "prerequisite": "CX4_PHYSICAL_PRINTER_PACKET_READY + real printer hardware",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Connect named printer; execute PHYSICAL_PRINTER_VALIDATION_PACKET",
            "person_org_needed": "Edmund / lab operator",
            "evidence_required": "CUPS collector bundle + physical output photos/hashes",
            "pass_rule": "successful USB or LAN path with job IDs + output integrity",
            "estimated_field_session_duration": "estimate 90-120 minutes",
            "status": "PENDING_PHYSICAL",
            "token_unlocked": "PHYSICAL_PRINTER_PENDING=false / physical_printer_pass",
        },
        {
            "blocker_id": "CX4-P-AV",
            "class": "Physical",
            "exact_requirement": "Camera/mic/AV quality + permission flows on real devices",
            "affected_product_sku": "Student 14.5 / Handheld Hybrid",
            "prerequisite": "CX4_CAMERA_MIC_AV_PACKET_READY + physical camera/mic",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Execute CAMERA_MIC_AV_VALIDATION_PACKET on hardware",
            "person_org_needed": "Edmund / AV lab",
            "evidence_required": "AV diagnostics + human quality notes + permission traces",
            "pass_rule": "field checklist complete; no severity-1 privacy/permission failures",
            "estimated_field_session_duration": "estimate 2 hours",
            "status": "PENDING_PHYSICAL",
            "token_unlocked": "PHYSICAL_CAMERA_MIC_AV_PENDING=false",
        },
        {
            "blocker_id": "CX4-P-PERIPH",
            "class": "Physical",
            "exact_requirement": "Peripheral matrix on real keyboard/mouse/touch/BT/dock/Ring",
            "affected_product_sku": "Device Quartet + Dock + Rings",
            "prerequisite": "CX4_PHYSICAL_PERIPHERAL_PACKET_READY",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Run peripheral matrix with named devices",
            "person_org_needed": "Edmund / hardware lab",
            "evidence_required": "Enumeration + mutation logs + reconnect evidence",
            "pass_rule": "per-device checks pass on real hardware",
            "estimated_field_session_duration": "estimate 2-3 hours",
            "status": "PENDING_PHYSICAL",
            "token_unlocked": "physical_peripheral_pass",
        },
        {
            "blocker_id": "CX4-P-EVT",
            "class": "Physical",
            "exact_requirement": "EVT bring-up for Device Quartet SKUs",
            "affected_product_sku": "Student 14.5 / Handheld / DS-XL / Rings / Dock",
            "prerequisite": "CX4_EVT_PACKET_READY + EVT boards",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Execute EVT packets on hardware",
            "person_org_needed": "Hardware eng + Edmund",
            "evidence_required": "EVT report per SKU",
            "pass_rule": "EVT gates green per SKU packet",
            "estimated_field_session_duration": "estimate multi-day (plan)",
            "status": "PENDING_PHYSICAL",
            "token_unlocked": "EVT_PENDING=false / evt_pass",
        },
        {
            "blocker_id": "CX4-P-DVT",
            "class": "Physical",
            "exact_requirement": "DVT sustained/thermal/mechanical/wireless coexistence",
            "affected_product_sku": "Device Quartet",
            "prerequisite": "EVT pass + CX4_DVT_PACKET_READY",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Execute DVT packets",
            "person_org_needed": "Hardware eng + test lab",
            "evidence_required": "DVT report per SKU",
            "pass_rule": "DVT gates green",
            "estimated_field_session_duration": "estimate multi-week (plan)",
            "status": "PENDING_PHYSICAL",
            "token_unlocked": "DVT_PENDING=false / dvt_pass",
        },
        {
            "blocker_id": "CX4-M-PVT",
            "class": "Manufacturing/business",
            "exact_requirement": "PVT manufacturing repeatability + factory diagnostics",
            "affected_product_sku": "Device Quartet",
            "prerequisite": "DVT pass + CX4_PVT_PACKET_READY + CX4_MANUFACTURING_PACKET_READY",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Engage CM/factory for PVT build",
            "person_org_needed": "Ops + CM + Edmund",
            "evidence_required": "PVT reports / yield / FAT",
            "pass_rule": "PVT gates green; manufacturing_pass still separate",
            "estimated_field_session_duration": "estimate multi-week (plan)",
            "status": "PENDING_MANUFACTURING",
            "token_unlocked": "PVT_PENDING=false / pvt_pass",
        },
        {
            "blocker_id": "CX4-E-CHAT",
            "class": "External provider",
            "exact_requirement": "External commercial chat/meeting provider evidence",
            "affected_product_sku": "Connect / collaboration",
            "prerequisite": "CX4_CHAT_MEETING_PROVIDER_READINESS_PASS",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Obtain provider credentials; run live provider validation",
            "person_org_needed": "Edmund + provider account owner",
            "evidence_required": "Live join/message/permission traces",
            "pass_rule": "REAL_PROVIDER_GUI_PASS for chosen external provider",
            "estimated_field_session_duration": "estimate 2 hours",
            "status": "PENDING_EXTERNAL",
            "token_unlocked": "external_provider_integration_pass / possible J4 upgrade",
        },
        {
            "blocker_id": "CX4-E-ISSUER",
            "class": "External provider",
            "exact_requirement": "Institutional issuer onboarding with real issuer",
            "affected_product_sku": "Wallet / Portfolio / Verifier",
            "prerequisite": "CX4_EXTERNAL_ISSUER_PACKET_READY",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Onboard a real institutional issuer in sandbox then production",
            "person_org_needed": "Issuer org + Edmund",
            "evidence_required": "Trust exchange + issued credential verify + revocation",
            "pass_rule": "issuer checklist complete; certification_claimed remains false unless earned",
            "estimated_field_session_duration": "estimate multi-day (plan)",
            "status": "PENDING_EXTERNAL",
            "token_unlocked": "external issuer integration evidence",
        },
        {
            "blocker_id": "CX4-L-PRIVACY-RIGHTS",
            "class": "Rights/legal",
            "exact_requirement": "Legal/privacy/rights review approval",
            "affected_product_sku": "All",
            "prerequisite": "CX4_PRIVACY_REVIEW_PACKET_READY + CX4_RIGHTS_REGISTER_READY",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Obtain counsel/privacy review against registers",
            "person_org_needed": "Legal/privacy counsel + Edmund",
            "evidence_required": "Signed review memo",
            "pass_rule": "legal_approval=true only after external review",
            "estimated_field_session_duration": "estimate calendar days (plan)",
            "status": "PENDING_LEGAL",
            "token_unlocked": "legal_approval",
        },
        {
            "blocker_id": "CX4-R-CERT",
            "class": "Regulatory/certification",
            "exact_requirement": "Regulatory certifications (FCC/CE/etc.)",
            "affected_product_sku": "Device Quartet radios/battery SKUs",
            "prerequisite": "CX4_CERTIFICATION_MATRIX_READY + hardware maturity",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Engage accredited test labs per matrix rows",
            "person_org_needed": "Compliance + test labs + Edmund",
            "evidence_required": "Lab reports / certificates",
            "pass_rule": "certified=true only with real certificates",
            "estimated_field_session_duration": "estimate multi-month (plan)",
            "status": "PENDING_REGULATORY",
            "token_unlocked": "certified",
        },
        {
            "blocker_id": "CX4-REL-WAIKE",
            "class": "Release dependency",
            "exact_requirement": "WAIKE earned credential integration on accepted-main release evidence",
            "affected_product_sku": "Education/Career",
            "prerequisite": "WAIKE release train completion (external to CX4)",
            "automatable_prework_complete": True,
            "minimal_real_world_action": "Do not modify WAIKE release; wait for genuine earned evidence then re-verify",
            "person_org_needed": "WAIKE release owners + Edmund",
            "evidence_required": "Real earned completion evidence on accepted-main",
            "pass_rule": "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS with real evidence",
            "estimated_field_session_duration": "blocked on release train",
            "status": "RELEASE_TRAIN_DEPENDENCY_PENDING",
            "token_unlocked": "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS",
        },
    ]
    return {
        "schema": "gunnchos.cx4.master_non_digital_blocker_register.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Contains only genuinely non-automatable remaining work.",
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "blockers": blockers,
    }


def write_edmund_action_packet(docs: Path) -> Dict[str, Any]:
    md = docs / "CX4_EDMUND_ACTION_PACKET.md"
    text = """# CX4 Edmund Action Packet (preparation — not evidence)

Ordered to minimize context switches. Only non-automatable human/physical/external actions.

## 1) Human accessibility session
- **Steps:** Execute `HUMAN_A11Y_VALIDATION_PACKET.md` with planned participants; store evidence under `artifacts/complete_experience/cx4_0/human_a11y/`.
- **Estimate:** 6–8 hours total (plan).
- **Prerequisite:** `CX4_HUMAN_A11Y_PACKET_READY`
- **Evidence:** observation forms, issues, screenshots/logs
- **Unlocks:** human a11y PASS / J6 class upgrade (only after real sessions)

## 2) Physical printer session
- **Steps:** Connect named USB and/or LAN printer; run `PHYSICAL_PRINTER_VALIDATION_PACKET.md`; run cups collector.
- **Estimate:** 90–120 minutes.
- **Prerequisite:** real printer hardware
- **Evidence:** collector bundle + output photos/hashes
- **Unlocks:** `PHYSICAL_PRINTER_PENDING` clearance

## 3) Camera / mic / AV session
- **Steps:** Execute `CAMERA_MIC_AV_VALIDATION_PACKET.md` on physical devices; capture diagnostics.
- **Estimate:** ~2 hours.
- **Prerequisite:** physical camera/mic
- **Evidence:** AV diag + quality notes
- **Unlocks:** `PHYSICAL_CAMERA_MIC_AV_PENDING` clearance

## 4) Peripheral matrix session
- **Steps:** Run peripheral matrix with keyboard/mouse/touch/BT/dock/Ring as available.
- **Estimate:** 2–3 hours.
- **Prerequisite:** named peripherals
- **Evidence:** mutation/reconnect logs
- **Unlocks:** physical peripheral PASS

## 5) Device Quartet EVT → DVT → PVT
- **Steps:** Follow per-SKU EVT/DVT/PVT packets; do not fabricate hardware.
- **Estimate:** multi-day to multi-week (plan).
- **Prerequisite:** hardware availability
- **Evidence:** stage reports
- **Unlocks:** EVT/DVT/PVT pending clearance

## 6) External chat/meeting provider credentials
- **Steps:** Obtain provider account; run live validation against contracts.
- **Estimate:** ~2 hours once credentials exist.
- **Prerequisite:** provider access
- **Evidence:** live traces
- **Unlocks:** external provider integration evidence (may upgrade J4)

## 7) Institutional issuer engagement
- **Steps:** Follow `CX4_INSTITUTIONAL_ISSUER_ONBOARDING.md` with a real issuer org.
- **Estimate:** multi-day (plan).
- **Prerequisite:** willing issuer
- **Evidence:** trust exchange + verify + revocation
- **Unlocks:** external issuer evidence (`certification_claimed` stays false unless earned)

## 8) Legal / privacy / rights review
- **Steps:** Submit privacy + rights registers for counsel review.
- **Estimate:** calendar days (plan).
- **Prerequisite:** registers ready
- **Evidence:** signed review memo
- **Unlocks:** `legal_approval`

## 9) Certification lab engagement
- **Steps:** Engage labs per `CERTIFICATION_MATRIX.json` rows when hardware maturity allows.
- **Estimate:** multi-month (plan).
- **Prerequisite:** EVT+/DVT hardware
- **Evidence:** certificates/reports
- **Unlocks:** `certified` (never from matrix alone)

## 10) WAIKE release dependency (do not modify release)
- **Steps:** Wait for genuine WAIKE accepted-main earned evidence; then re-verify CX3 earned token.
- **Estimate:** blocked on release train.
- **Prerequisite:** WAIKE release owners
- **Evidence:** real earned completion artifacts
- **Unlocks:** `CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS`

This packet is preparation, not evidence. `CX4_OWNER_ACTION_PACKET_READY=true` does not complete any gate.
"""
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(text)
    return {"ready": True, "path": str(md), "automatable_actions_included": False}


def write_master_register(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    docs = readiness_docs_root(repo)
    docs.mkdir(parents=True, exist_ok=True)
    reg = build_blocker_register()
    path = docs / "CX4_MASTER_NON_DIGITAL_BLOCKER_REGISTER.json"
    path.write_text(json.dumps(reg, indent=2) + "\n")
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "CX4_MASTER_NON_DIGITAL_BLOCKER_REGISTER.json").write_text(json.dumps(reg, indent=2) + "\n")
    edmund = write_edmund_action_packet(docs)
    (ev / "CX4_EDMUND_ACTION_PACKET_POINTER.json").write_text(json.dumps(edmund, indent=2) + "\n")
    return {"register": reg, "register_path": str(path), "edmund": edmund}
