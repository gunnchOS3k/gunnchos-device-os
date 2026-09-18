"""CX3.3 truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx33Tokens:
    # Rebind
    CX3_3_REBIND_PASS: bool = False

    # Retained CX3.1 (prompt aliases + foundation)
    CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS: bool = False
    CX3_REAL_SIGNED_ISSUER_PASS: bool = False
    CX3_REAL_EVIDENCE_BOUND_ISSUANCE_PASS: bool = False
    CX3_WALLET_SECURE_STORAGE_PASS: bool = False
    CX3_REAL_WALLET_GUI_PASS: bool = False
    CX3_REAL_SIGNED_CREDENTIAL_JOURNEY_PASS: bool = False
    CX3_TAMPER_DETECTION_PASS: bool = False
    CX3_REVOCATION_STATUS_PASS: bool = False
    CX3_OFFLINE_VERIFY_PASS: bool = False
    CX3_CREDENTIAL_IMPORT_EXPORT_PASS: bool = False
    CX3_REAL_PORTFOLIO_GUI_PASS: bool = False
    CX3_PORTFOLIO_PRIVACY_PASS: bool = False
    CX3_PORTABLE_PORTFOLIO_EXPORT_PASS: bool = False

    # Retained CX3.2
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
    CX3_2_CAREER_VERIFIER_PASS: bool = False

    # WAIKE
    WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE: bool = False
    CX3_WAIKE_READ_ONLY_PROVIDER_PASS: bool = False
    CX3_WAIKE_EVIDENCE_PROVENANCE_PASS: bool = False
    CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS: bool = False
    CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS: bool = False

    # CX3.3 digital closure lanes
    CX3_EDUCATION_TIMELINE_PASS: bool = False
    CX3_SKILL_EVIDENCE_GRAPH_PASS: bool = False
    CX3_CAREER_PACKAGE_PASS: bool = False
    CX3_CAREER_PACKAGE_RECOVERY_PASS: bool = False
    CX3_VERIFIER_MATRIX_PASS: bool = False
    CX3_AUTOMATED_A11Y_PASS: bool = False
    CX3_NO_SECOND_COMPUTER_FINAL_PASS: bool = False
    CX3_3_SECURITY_REGRESSION_FREE: bool = False
    CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS: bool = False

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

    def digital_closure_eligible(self) -> bool:
        """Generic CX3 digital closure — WAIKE earned may remain false."""
        return bool(
            self.CX3_3_REBIND_PASS
            and self.CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS
            and self.CX3_2_CAREER_VERIFIER_PASS
            and self.CX3_EDUCATION_TIMELINE_PASS
            and self.CX3_SKILL_EVIDENCE_GRAPH_PASS
            and self.CX3_CAREER_PACKAGE_PASS
            and self.CX3_CAREER_PACKAGE_RECOVERY_PASS
            and self.CX3_VERIFIER_MATRIX_PASS
            and self.CX3_AUTOMATED_A11Y_PASS
            and self.CX3_NO_SECOND_COMPUTER_FINAL_PASS
            and self.CX3_3_SECURITY_REGRESSION_FREE
            and self.CX3_CERTIFICATION_CLAIMED is False
            and not self.FULL_COMPLETE_EXPERIENCE_COMPLETE
            and not self.lab_blocker
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx33Tokens)]
