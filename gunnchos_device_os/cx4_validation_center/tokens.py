"""CX4.1 + CX4.2 Validation Center truth tokens — software readiness ≠ human/physical PASS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx41Tokens:
    # Software capability tokens (CX4.1)
    CX4_VALIDATION_CENTER_GUI_PASS: bool = False
    CX4_VALIDATION_TASK_LIBRARY_PASS: bool = False
    CX4_VALIDATION_RATING_UI_PASS: bool = False
    CX4_VALIDATION_EVIDENCE_CAPTURE_PASS: bool = False
    CX4_VALIDATION_CENTER_OFFLINE_AUTOSAVE_PASS: bool = False
    CX4_VALIDATION_SUBMISSION_BUNDLE_PASS: bool = False
    CX4_VALIDATION_REVIEWER_SIGNOFF_ENFORCED: bool = True
    CX4_EDMUND_ACTION_PACKET_UI_MAPPED: bool = False
    CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS: bool = False
    CX4_VALIDATION_CENTER_SECURITY_PASS: bool = False
    MINORS_MODE_DISABLED_BY_DEFAULT: bool = True

    # CX4.2 pilot readiness tokens
    CX4_VALIDATION_CENTER_ONE_CLICK_LAUNCH_PASS: bool = False
    CX4_PARTICIPANT_ENTRY_FLOW_PASS: bool = False
    CX4_MODERATOR_SESSION_WIZARD_PASS: bool = False
    CX4_PARTICIPANT_ACCESSIBILITY_RENDERED_PASS: bool = False
    CX4_PARTICIPANT_RATING_FLOW_PASS: bool = False
    CX4_HUMAN_EVIDENCE_CAPTURE_UX_PASS: bool = False
    CX4_REVIEWER_WORKFLOW_PASS: bool = False
    CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS: bool = False
    CX4_VALIDATION_MATERIALITY_ENGINE_PASS: bool = False
    CX4_VALIDATION_REHEARSAL_FLOW_PASS: bool = False
    CX4_HUMAN_VALIDATION_DAY_PACKET_READY: bool = False
    CX4_VALIDATION_EXPORT_RECOVERY_PASS: bool = False
    CX4_VALIDATION_UI_COMPATIBILITY_PASS: bool = False
    CX4_VALIDATION_PILOT_SECURITY_PASS: bool = False
    CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE: bool = False

    # Inherited CX4.0 readiness (software prep already done)
    CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS: bool = True

    # Kept pending — never flipped by Validation Center software alone
    J6_CLASS: str = "HUMAN_VALIDATION_PENDING"
    PHYSICAL_PRINTER_PENDING: bool = True
    PHYSICAL_CAMERA_MIC_AV_PENDING: bool = True
    EVT_PENDING: bool = True
    DVT_PENDING: bool = True
    PVT_PENDING: bool = True
    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    human_a11y_pass: bool = False
    physical_printer_pass: bool = False
    physical_camera_mic_av_pass: bool = False
    evt_pass: bool = False
    dvt_pass: bool = False
    pvt_pass: bool = False
    certification_claimed: bool = False
    certified: bool = False
    legal_approval: bool = False
    manufacturing_pass: bool = False
    external_provider_integration_pass: bool = False

    # Counts (truthful; start at 0; rehearsal excluded)
    real_human_sessions_count: int = 0
    reviewer_signed_sessions_count: int = 0
    rehearsal_sessions_count: int = 0

    # Firewall
    CX4_DEVICE_LAB_134_UNALTERED: bool = True
    CX4_PORTAL_14_UNALTERED: bool = True
    CX4_PORTAL_15_UNALTERED: bool = True
    CX4_WAIKE_RELEASE_UNALTERED: bool = True
    CX4_NO_MERGES: bool = True
    CX4_NO_DEVICE_LAB: bool = True
    CX4_NO_QEMU_DEFAULT: bool = True

    NEXT_CX_ACTION: str = "COMPLETE_VALIDATION_CENTER_PILOT_READINESS"

    notes: str = ""

    def software_complete(self) -> bool:
        return bool(
            self.CX4_VALIDATION_CENTER_GUI_PASS
            and self.CX4_VALIDATION_TASK_LIBRARY_PASS
            and self.CX4_VALIDATION_RATING_UI_PASS
            and self.CX4_VALIDATION_EVIDENCE_CAPTURE_PASS
            and self.CX4_VALIDATION_CENTER_OFFLINE_AUTOSAVE_PASS
            and self.CX4_VALIDATION_SUBMISSION_BUNDLE_PASS
            and self.CX4_VALIDATION_REVIEWER_SIGNOFF_ENFORCED
            and self.CX4_EDMUND_ACTION_PACKET_UI_MAPPED
            and self.CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS
            and self.CX4_VALIDATION_CENTER_SECURITY_PASS
            and self.MINORS_MODE_DISABLED_BY_DEFAULT
            and self.J6_CLASS == "HUMAN_VALIDATION_PENDING"
            and self.PHYSICAL_PRINTER_PENDING
            and self.PHYSICAL_CAMERA_MIC_AV_PENDING
            and self.EVT_PENDING
            and self.DVT_PENDING
            and self.PVT_PENDING
            and not self.FULL_COMPLETE_EXPERIENCE_COMPLETE
            and not self.human_a11y_pass
            and not self.physical_printer_pass
            and not self.evt_pass
            and not self.dvt_pass
            and not self.pvt_pass
        )

    def pilot_readiness_complete(self) -> bool:
        return bool(
            self.software_complete()
            and self.CX4_VALIDATION_CENTER_ONE_CLICK_LAUNCH_PASS
            and self.CX4_PARTICIPANT_ENTRY_FLOW_PASS
            and self.CX4_MODERATOR_SESSION_WIZARD_PASS
            and self.CX4_PARTICIPANT_ACCESSIBILITY_RENDERED_PASS
            and self.CX4_PARTICIPANT_RATING_FLOW_PASS
            and self.CX4_HUMAN_EVIDENCE_CAPTURE_UX_PASS
            and self.CX4_REVIEWER_WORKFLOW_PASS
            and self.CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS
            and self.CX4_VALIDATION_MATERIALITY_ENGINE_PASS
            and self.CX4_VALIDATION_REHEARSAL_FLOW_PASS
            and self.CX4_HUMAN_VALIDATION_DAY_PACKET_READY
            and self.CX4_VALIDATION_EXPORT_RECOVERY_PASS
            and self.CX4_VALIDATION_UI_COMPATIBILITY_PASS
            and self.CX4_VALIDATION_PILOT_SECURITY_PASS
            and not self.CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE
        )

    def preferred_next_action(self) -> str:
        if self.pilot_readiness_complete():
            return "WAIT_FOR_FINAL_ACCEPTED_BUILD_THEN_RUN_HUMAN_VALIDATION"
        if self.software_complete():
            return "COMPLETE_VALIDATION_CENTER_PILOT_READINESS"
        return "COMPLETE_VALIDATION_CENTER_SOFTWARE"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["NEXT_CX_ACTION"] = self.preferred_next_action()
        d["CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE"] = False
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cx41Tokens":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


# Alias for CX4.2 naming clarity
Cx42Tokens = Cx41Tokens
