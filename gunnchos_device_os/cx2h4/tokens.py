"""CX2H.4 truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2h4Tokens:
    CX2H4_JOURNEY_REBIND_PASS: bool = False
    CX2H4_J4_P0_DIGITAL_BLOCKER: bool = True
    CX2H4_SPREADSHEET_P0_PASS: bool = False
    CX2H4_PRESENTATION_P0_PASS: bool = False
    CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS: str = "not_required"  # true|false|not_required
    CX2H4_DEVELOPER_BASELINE_PASS: str = "not_required"
    CX2H4_NO_SECOND_COMPUTER_P0_PASS: bool = False
    CX2H4_SECURITY_REGRESSION_FREE: bool = False
    CX2H4_P0_DIGITAL_CLOSURE_PASS: bool = False

    CX2H_DEVICE_LAB_134_UNALTERED: bool = True
    CX2H_PORTAL_14_UNALTERED: bool = True
    CX2H_PORTAL_15_UNALTERED: bool = True
    CX2H_DEVICE_LAB_MANIFEST_UNALTERED: bool = True
    CX2H_NO_MERGES: bool = True
    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    guest_booted: bool = False
    guest_is_linux: bool = False
    lab_blocker: str = ""
    notes: str = ""

    J1_CLASS: str = "BLOCKED"
    J2_CLASS: str = "BLOCKED"
    J3_CLASS: str = "BLOCKED"
    J4_CLASS: str = "BLOCKED"
    J5_CLASS: str = "BLOCKED"
    J6_CLASS: str = "HUMAN_VALIDATION_PENDING"
    J7_CLASS: str = "BLOCKED"

    def digital_closure_eligible(self) -> bool:
        media_ok = self.CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS in ("true", "not_required", True)
        if self.CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS is True:
            media_ok = True
        if self.CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS is False or self.CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS == "false":
            media_ok = False
        dev_ok = self.CX2H4_DEVELOPER_BASELINE_PASS in ("true", "not_required", True)
        if self.CX2H4_DEVELOPER_BASELINE_PASS is False or self.CX2H4_DEVELOPER_BASELINE_PASS == "false":
            dev_ok = False
        return bool(
            self.CX2H4_JOURNEY_REBIND_PASS
            and not self.CX2H4_J4_P0_DIGITAL_BLOCKER
            and self.CX2H4_SPREADSHEET_P0_PASS
            and self.CX2H4_PRESENTATION_P0_PASS
            and media_ok
            and dev_ok
            and self.CX2H4_NO_SECOND_COMPUTER_P0_PASS
            and self.CX2H4_SECURITY_REGRESSION_FREE
            and self.J1_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J2_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J3_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J5_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J7_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J6_CLASS == "HUMAN_VALIDATION_PENDING"
            and not self.FULL_COMPLETE_EXPERIENCE_COMPLETE
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # normalize string tokens for JSON consumers
        for k in ("CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS", "CX2H4_DEVELOPER_BASELINE_PASS"):
            v = d[k]
            if v is True:
                d[k] = "true"
            elif v is False:
                d[k] = "false"
        return d


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2h4Tokens)]
