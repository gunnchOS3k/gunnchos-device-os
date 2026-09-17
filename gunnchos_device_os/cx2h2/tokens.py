"""CX2H.2 truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2h2Tokens:
    # Re-proven shell + J3 prereqs
    CX2H_SHELL_PREREQ_PASS: bool = False
    CX2H_CHROMIUM_RUNTIME_PASS: bool = False
    CX2H_WAYLAND_SURFACE_PASS: bool = False
    CX2H_GUNNCH_SHELL_RENDER_PASS: bool = False
    CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS: bool = False
    CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS: bool = False
    CX2H_REAL_APP_CENTER_WINDOW: bool = False
    CX2H_XDG_PORTAL_SESSION_PASS: bool = False
    J3_CLASS: str = "BLOCKED"

    # CX2H.2 product tokens
    CX2H2_REAL_WRITER_GUI_PASS: bool = False
    CX2H2_REAL_VAULT_FILE_PASS: bool = False
    CX2H2_REAL_PDF_EXPORT_GUI_PASS: bool = False
    CX2H2_REAL_IPP_PROVIDER_PASS: bool = False
    CX2H2_REAL_IPP_PRINT_GUI_PASS: bool = False
    CX2H2_REAL_BACKUP_GUI_PASS: bool = False
    CX2H2_REAL_RESTORE_GUI_PASS: bool = False
    CX2H2_PHYSICAL_PRINTER_PENDING: bool = True
    CX2H2_PERSISTENCE_PASS: bool = False
    CX2H_HUMAN_A11Y_PENDING: bool = True

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
    J4_CLASS: str = "BLOCKED"
    J5_CLASS: str = "BLOCKED"
    J6_CLASS: str = "HUMAN_VALIDATION_PENDING"
    J7_CLASS: str = "BLOCKED"

    def gate_shell_prereq(self) -> bool:
        return bool(
            self.CX2H_SHELL_PREREQ_PASS
            and self.CX2H_CHROMIUM_RUNTIME_PASS
            and self.CX2H_WAYLAND_SURFACE_PASS
            and self.CX2H_GUNNCH_SHELL_RENDER_PASS
            and self.CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS
            and self.CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS
            and self.CX2H_REAL_APP_CENTER_WINDOW
            and self.CX2H_XDG_PORTAL_SESSION_PASS
            and self.J3_CLASS == "REAL_USER_JOURNEY_DIGITAL_PASS"
        )

    def j1_digital_pass(self) -> bool:
        return bool(
            self.gate_shell_prereq()
            and self.CX2H2_REAL_WRITER_GUI_PASS
            and self.CX2H2_REAL_VAULT_FILE_PASS
            and self.CX2H2_REAL_PDF_EXPORT_GUI_PASS
            and self.CX2H2_REAL_IPP_PROVIDER_PASS
            and self.CX2H2_REAL_IPP_PRINT_GUI_PASS
            and self.CX2H2_REAL_BACKUP_GUI_PASS
            and self.CX2H2_REAL_RESTORE_GUI_PASS
            and self.CX2H2_PERSISTENCE_PASS
            and self.CX2H2_PHYSICAL_PRINTER_PENDING
        )

    def j7_digital_pass(self) -> bool:
        return bool(
            self.gate_shell_prereq()
            and self.CX2H2_REAL_BACKUP_GUI_PASS
            and self.CX2H2_REAL_RESTORE_GUI_PASS
            and self.CX2H2_REAL_WRITER_GUI_PASS
            and self.CX2H2_PERSISTENCE_PASS
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2h2Tokens)]
