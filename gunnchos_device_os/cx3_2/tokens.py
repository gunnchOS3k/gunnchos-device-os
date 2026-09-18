"""CX3.2 truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx32Tokens:
    # Retained foundation
    CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS: bool = False
    CX2H4_P0_DIGITAL_CLOSURE_PASS: bool = False

    # Track A
    WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE: bool = False
    CX3_WAIKE_READ_ONLY_PROVIDER_PASS: bool = False
    CX3_WAIKE_EVIDENCE_PROVENANCE_PASS: bool = False
    CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS: bool = False
    CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS: bool = False

    # Track B
    CX3_REAL_CAREER_PROFILE_GUI_PASS: bool = False
    CX3_RESUME_EXPORT_PASS: bool = False
    CX3_PORTFOLIO_SHARE_PACKAGE_PASS: bool = False
    CX3_INDEPENDENT_VERIFIER_PASS: bool = False
    CX3_REAL_VERIFIER_GUI_PASS: bool = False
    CX3_SELECTIVE_DISCLOSURE_PASS: bool = False
    CX3_VERIFIER_REVOCATION_PROPAGATION_PASS: bool = False
    CX3_OFFLINE_CAREER_VERIFIER_PASS: bool = False
    CX3_NO_SECOND_COMPUTER_CAREER_PASS: bool = False
    CX3_2_SECURITY_REGRESSION_FREE: bool = False

    # Campaign aggregate
    CX3_2_CAREER_VERIFIER_PASS: bool = False

    # Firewall
    CX3_DEVICE_LAB_134_UNALTERED: bool = True
    CX3_PORTAL_14_UNALTERED: bool = True
    CX3_PORTAL_15_UNALTERED: bool = True
    CX3_WAIKE_RELEASE_UNALTERED: bool = True
    CX3_NO_MERGES: bool = True
    CX3_NO_DEVICE_LAB: bool = True
    CX3_CERTIFICATION_CLAIMED: bool = False

    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    guest_booted: bool = False
    guest_is_linux: bool = False
    lab_blocker: str = ""
    waike_blocker: str = ""
    notes: str = ""

    J1_CLASS: str = "BLOCKED"
    J2_CLASS: str = "BLOCKED"
    J3_CLASS: str = "BLOCKED"
    J4_CLASS: str = "BLOCKED"
    J5_CLASS: str = "BLOCKED"
    J6_CLASS: str = "HUMAN_VALIDATION_PENDING"
    J7_CLASS: str = "BLOCKED"

    def career_verifier_eligible(self) -> bool:
        return bool(
            self.CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS
            and self.CX3_REAL_CAREER_PROFILE_GUI_PASS
            and self.CX3_RESUME_EXPORT_PASS
            and self.CX3_PORTFOLIO_SHARE_PACKAGE_PASS
            and self.CX3_INDEPENDENT_VERIFIER_PASS
            and self.CX3_REAL_VERIFIER_GUI_PASS
            and self.CX3_SELECTIVE_DISCLOSURE_PASS
            and self.CX3_VERIFIER_REVOCATION_PROPAGATION_PASS
            and self.CX3_OFFLINE_CAREER_VERIFIER_PASS
            and self.CX3_NO_SECOND_COMPUTER_CAREER_PASS
            and self.CX3_2_SECURITY_REGRESSION_FREE
            and self.CX3_CERTIFICATION_CLAIMED is False
            and not self.FULL_COMPLETE_EXPERIENCE_COMPLETE
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx32Tokens)]
