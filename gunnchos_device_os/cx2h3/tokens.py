"""CX2H.3 truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2h3Tokens:
    CX2H3_PREREQUISITE_PASS: bool = False
    CX2H3_REAL_HTTPS_PROVIDER_PASS: bool = False
    CX2H3_REAL_BROWSER_GUI_PASS: bool = False
    CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS: bool = False
    CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS: bool = False
    CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS: bool = False
    CX2H3_REAL_MAIL_GUI_PASS: bool = False
    CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS: bool = False
    CX2H3_J2_PERSISTENCE_PASS: bool = False

    CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS: bool = False
    CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS: bool = False
    CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS: bool = False
    CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS: bool = False
    CX2H3_RECONNECT_FAILURE_RECOVERY_PASS: bool = False

    # Retained prior-wave truth (rebind)
    CX2H_SHELL_PREREQ_PASS: bool = False
    CX2H_XDG_PORTAL_SESSION_PASS: bool = False
    CX2H2_REAL_WRITER_GUI_PASS: bool = False
    CX2H2_REAL_VAULT_FILE_PASS: bool = False

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

    def j2_digital_pass(self) -> bool:
        return bool(
            self.CX2H3_PREREQUISITE_PASS
            and self.CX2H3_REAL_HTTPS_PROVIDER_PASS
            and self.CX2H3_REAL_BROWSER_GUI_PASS
            and self.CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS
            and self.CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS
            and self.CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS
            and self.CX2H3_REAL_MAIL_GUI_PASS
            and self.CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS
            and self.CX2H3_J2_PERSISTENCE_PASS
            and self.J1_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J3_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
            and self.J7_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
        )

    def j5_digital_pass(self) -> bool:
        return bool(
            self.j2_digital_pass()
            and self.CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS
            and self.CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS
            and self.CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS
            and self.CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS
            and self.CX2H3_RECONNECT_FAILURE_RECOVERY_PASS
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2h3Tokens)]
