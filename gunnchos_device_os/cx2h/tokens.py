"""CX2H truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2hTokens:
    # Re-proven CX2G shell prerequisites (namespaced for CX2H evidence)
    CX2H_SHELL_PREREQ_PASS: bool = False
    CX2H_CHROMIUM_RUNTIME_PASS: bool = False
    CX2H_WAYLAND_SURFACE_PASS: bool = False
    CX2H_GUNNCH_SHELL_RENDER_PASS: bool = False
    CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS: bool = False
    CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS: bool = False
    CX2H_REAL_APP_CENTER_WINDOW: bool = False

    CX2H_XDG_PORTAL_SESSION_PASS: bool = False
    CX2H_REAL_APP_CENTER_PROVIDER_PASS: bool = False
    CX2H_REAL_APP_INSTALL_GUI_PASS: bool = False
    CX2H_REAL_APP_UPDATE_GUI_PASS: bool = False
    CX2H_REAL_APP_ROLLBACK_GUI_PASS: bool = False
    CX2H_REAL_APP_UNINSTALL_GUI_PASS: bool = False
    CX2H_REAL_APP_LAUNCH_GUI_PASS: bool = False
    CX2H_J3_PERSISTENCE_PASS: bool = False

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

    def gate_shell_prereq(self) -> bool:
        return bool(
            self.CX2H_SHELL_PREREQ_PASS
            and self.CX2H_CHROMIUM_RUNTIME_PASS
            and self.CX2H_WAYLAND_SURFACE_PASS
            and self.CX2H_GUNNCH_SHELL_RENDER_PASS
            and self.CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS
            and self.CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS
            and self.CX2H_REAL_APP_CENTER_WINDOW
        )

    def j3_digital_pass(self) -> bool:
        return bool(
            self.gate_shell_prereq()
            and self.CX2H_XDG_PORTAL_SESSION_PASS
            and self.CX2H_REAL_APP_CENTER_PROVIDER_PASS
            and self.CX2H_REAL_APP_INSTALL_GUI_PASS
            and self.CX2H_REAL_APP_LAUNCH_GUI_PASS
            and self.CX2H_REAL_APP_UPDATE_GUI_PASS
            and self.CX2H_REAL_APP_UNINSTALL_GUI_PASS
            and self.CX2H_J3_PERSISTENCE_PASS
            # rollback optional if provider cannot; token stays false unless proven
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2hTokens)]
