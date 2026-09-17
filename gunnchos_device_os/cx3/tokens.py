"""CX3.1 truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx3Tokens:
    # Prior gate retained
    CX2H4_P0_DIGITAL_CLOSURE_PASS: bool = False

    # CX3.1 foundation tokens
    CX3_CONTRACTS_V1_PASS: bool = False
    CX3_LAB_ISSUER_ED25519_PASS: bool = False
    CX3_EVIDENCE_BOUND_ISSUANCE_PASS: bool = False
    CX3_WALLET_STORAGE_PASS: bool = False
    CX3_WALLET_GUI_PASS: bool = False
    CX3_SIGNED_CREDENTIAL_JOURNEY_PASS: bool = False
    CX3_TAMPER_DETECT_PASS: bool = False
    CX3_REVOCATION_STATUS_PASS: bool = False
    CX3_OFFLINE_VERIFY_PASS: bool = False
    CX3_IMPORT_EXPORT_PASS: bool = False
    CX3_PORTFOLIO_GUI_PASS: bool = False
    CX3_PORTFOLIO_PRIVACY_EXPORT_PASS: bool = False
    CX3_PORTFOLIO_PORTABLE_PACKAGE_PASS: bool = False
    CX3_SECURITY_FAIL_CLOSED_PASS: bool = False
    CX3_OB3_CLR_ADAPTER_PASS: bool = False
    WAIKE_INTEGRATION_SEAM_PASS: bool = False
    WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS: bool = False
    CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS: bool = False

    # Firewall
    CX3_DEVICE_LAB_134_UNALTERED: bool = True
    CX3_PORTAL_14_UNALTERED: bool = True
    CX3_PORTAL_15_UNALTERED: bool = True
    CX3_WAIKE_RELEASE_UNALTERED: bool = True
    CX3_NO_MERGES: bool = True
    CX3_NO_DEVICE_LAB: bool = True
    CX3_CERTIFICATION_CLAIMED: bool = False  # must always stay false

    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    guest_booted: bool = False
    guest_is_linux: bool = False
    lab_blocker: str = ""
    notes: str = ""

    # Journey classes retained from CX2H4
    J1_CLASS: str = "BLOCKED"
    J2_CLASS: str = "BLOCKED"
    J3_CLASS: str = "BLOCKED"
    J4_CLASS: str = "BLOCKED"
    J5_CLASS: str = "BLOCKED"
    J6_CLASS: str = "HUMAN_VALIDATION_PENDING"
    J7_CLASS: str = "BLOCKED"

    def foundation_eligible(self) -> bool:
        """Wallet + portfolio foundation may PASS without WAIKE earned integration."""
        return bool(
            self.CX2H4_P0_DIGITAL_CLOSURE_PASS
            and self.CX3_CONTRACTS_V1_PASS
            and self.CX3_LAB_ISSUER_ED25519_PASS
            and self.CX3_EVIDENCE_BOUND_ISSUANCE_PASS
            and self.CX3_WALLET_STORAGE_PASS
            and self.CX3_WALLET_GUI_PASS
            and self.CX3_SIGNED_CREDENTIAL_JOURNEY_PASS
            and self.CX3_TAMPER_DETECT_PASS
            and self.CX3_REVOCATION_STATUS_PASS
            and self.CX3_OFFLINE_VERIFY_PASS
            and self.CX3_IMPORT_EXPORT_PASS
            and self.CX3_PORTFOLIO_GUI_PASS
            and self.CX3_PORTFOLIO_PRIVACY_EXPORT_PASS
            and self.CX3_PORTFOLIO_PORTABLE_PACKAGE_PASS
            and self.CX3_SECURITY_FAIL_CLOSED_PASS
            and self.CX3_OB3_CLR_ADAPTER_PASS
            and self.WAIKE_INTEGRATION_SEAM_PASS
            and self.CX3_CERTIFICATION_CLAIMED is False
            and not self.FULL_COMPLETE_EXPERIENCE_COMPLETE
            and self.J1_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J2_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J3_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J5_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J7_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J6_CLASS == "HUMAN_VALIDATION_PENDING"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx3Tokens)]
