"""CX4 truth tokens — readiness ≠ PASS for human/physical/external gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx4Tokens:
    # Guest rebind
    CX4_CURRENT_TIP_GUEST_OVERLAY_PASS: bool = False
    CX4_CURRENT_TIP_GUEST_SMOKE_PASS: bool = False

    # Readiness packets (automatable prep)
    CX4_HUMAN_A11Y_PACKET_READY: bool = False
    CX4_PHYSICAL_PRINTER_PACKET_READY: bool = False
    CX4_CAMERA_MIC_AV_PACKET_READY: bool = False
    CX4_PHYSICAL_PERIPHERAL_PACKET_READY: bool = False
    CX4_EVT_PACKET_READY: bool = False
    CX4_DVT_PACKET_READY: bool = False
    CX4_PVT_PACKET_READY: bool = False
    CX4_FIRMWARE_LIFECYCLE_PACKET_READY: bool = False
    CX4_SUPPORT_BUNDLE_READY: bool = False
    CX4_REPAIR_RMA_PACKET_READY: bool = False
    CX4_CHAT_MEETING_PROVIDER_READINESS_PASS: bool = False
    CX4_EXTERNAL_ISSUER_PACKET_READY: bool = False
    CX4_PRIVACY_REVIEW_PACKET_READY: bool = False
    CX4_RIGHTS_REGISTER_READY: bool = False
    CX4_CERTIFICATION_MATRIX_READY: bool = False
    CX4_MANUFACTURING_PACKET_READY: bool = False
    CX4_OWNER_ACTION_PACKET_READY: bool = False
    CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS: bool = False

    # Kept pending — never flipped by preparation alone
    J6_CLASS: str = "HUMAN_VALIDATION_PENDING"
    PHYSICAL_PRINTER_PENDING: bool = True
    PHYSICAL_CAMERA_MIC_AV_PENDING: bool = True
    EVT_PENDING: bool = True
    DVT_PENDING: bool = True
    PVT_PENDING: bool = True
    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    certification_claimed: bool = False
    certified: bool = False
    legal_approval: bool = False
    manufacturing_pass: bool = False
    physical_printer_pass: bool = False
    physical_camera_mic_av_pass: bool = False
    human_a11y_pass: bool = False
    evt_pass: bool = False
    dvt_pass: bool = False
    pvt_pass: bool = False
    external_provider_integration_pass: bool = False

    # Firewall
    CX4_DEVICE_LAB_134_UNALTERED: bool = True
    CX4_PORTAL_14_UNALTERED: bool = True
    CX4_PORTAL_15_UNALTERED: bool = True
    CX4_WAIKE_RELEASE_UNALTERED: bool = True
    CX4_NO_MERGES: bool = True
    CX4_NO_DEVICE_LAB: bool = True

    # Inherited CX3 truth retained
    CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS: bool = True
    CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS: bool = False
    WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE: bool = False

    lab_blocker: str = ""
    notes: str = ""

    def readiness_complete(self) -> bool:
        return bool(
            self.CX4_CURRENT_TIP_GUEST_OVERLAY_PASS
            and self.CX4_CURRENT_TIP_GUEST_SMOKE_PASS
            and self.CX4_HUMAN_A11Y_PACKET_READY
            and self.CX4_PHYSICAL_PRINTER_PACKET_READY
            and self.CX4_CAMERA_MIC_AV_PACKET_READY
            and self.CX4_PHYSICAL_PERIPHERAL_PACKET_READY
            and self.CX4_EVT_PACKET_READY
            and self.CX4_DVT_PACKET_READY
            and self.CX4_PVT_PACKET_READY
            and self.CX4_FIRMWARE_LIFECYCLE_PACKET_READY
            and self.CX4_SUPPORT_BUNDLE_READY
            and self.CX4_REPAIR_RMA_PACKET_READY
            and self.CX4_CHAT_MEETING_PROVIDER_READINESS_PASS
            and self.CX4_EXTERNAL_ISSUER_PACKET_READY
            and self.CX4_PRIVACY_REVIEW_PACKET_READY
            and self.CX4_RIGHTS_REGISTER_READY
            and self.CX4_CERTIFICATION_MATRIX_READY
            and self.CX4_MANUFACTURING_PACKET_READY
            and self.CX4_OWNER_ACTION_PACKET_READY
            and self.J6_CLASS == "HUMAN_VALIDATION_PENDING"
            and self.PHYSICAL_PRINTER_PENDING
            and self.PHYSICAL_CAMERA_MIC_AV_PENDING
            and self.EVT_PENDING
            and self.DVT_PENDING
            and self.PVT_PENDING
            and not self.FULL_COMPLETE_EXPERIENCE_COMPLETE
            and not self.certification_claimed
            and not self.certified
            and not self.legal_approval
            and not self.manufacturing_pass
            and not self.physical_printer_pass
            and not self.physical_camera_mic_av_pass
            and not self.human_a11y_pass
            and not self.evt_pass
            and not self.dvt_pass
            and not self.pvt_pass
            and not self.external_provider_integration_pass
            and not self.lab_blocker
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cx4Tokens":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
