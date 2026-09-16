"""CX2F truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2fTokens:
    CX2F_NON_CLOUD_KERNEL_SELECTED: bool = False
    CX2F_NON_CLOUD_KERNEL_BOOT_PASS: bool = False
    CX2F_VIRTIO_GPU_ENUMERATION_PASS: bool = False
    CX2F_DRM_CARD_PASS: bool = False
    CX2F_DRM_RENDER_NODE_PASS: bool = False
    CX2F_QEMU_GRAPHICS_SURFACE_PASS: bool = False
    CX2F_WESTON_DRM_PASS: bool = False
    CX2F_WESTON_HEADLESS_FALLBACK_USED: bool = False
    CX2F_WAYLAND_SOCKET_PASS: bool = False
    CX2F_DBUS_SESSION_PASS: bool = False
    CX2F_SHELL_ASSET_DELIVERY_PASS: bool = False
    CX2F_GUNNCH_SHELL_RENDER_PASS: bool = False
    CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS: bool = False
    CX2F_RENDER_CAPTURE_PASS: bool = False
    CX2F_REAL_SCREEN_CAPTURE_PASS: bool = False
    CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS: bool = False
    CX2F_XDG_PORTAL_SESSION_PASS: bool = False
    CX2F_REAL_HOME_WINDOW: bool = False
    CX2F_REAL_VAULT_WINDOW: bool = False
    CX2F_REAL_APP_CENTER_WINDOW: bool = False
    CX2F_REAL_CONNECT_WINDOW: bool = False
    CX2F_REAL_ASSIST_WINDOW: bool = False
    CX2F_REAL_CARE_WINDOW: bool = False
    CX2F_REAL_BROWSER_GUI_PASS: bool = False
    CX2F_REAL_APP_LIFECYCLE_GUI_PASS: bool = False
    CX2F_REAL_PRODUCTIVITY_GUI_PASS: bool = False
    CX2F_REAL_MAIL_GUI_PASS: bool = False
    CX2F_REAL_CALDAV_CARDDAV_GUI_PASS: bool = False
    CX2F_REAL_IPP_GUI_DIGITAL_PASS: bool = False
    CX2F_DIGITAL_RENDERED_A11Y_PASS: bool = False
    CX2F_REAL_OFFLINE_RECOVERY_GUI_PASS: bool = False
    CX2F_HUMAN_A11Y_PENDING: bool = True
    CX2F_PHYSICAL_PRINTER_PENDING: bool = True
    CX2F_HUMAN_AV_QUALITY_PENDING: bool = True
    CX2F_PHYSICAL_CAMERA_MIC_PENDING: bool = True
    CX2F_SINGLE_PRODUCTION_SHELL_AUTHORITY: bool = True
    CX2F_DEVICE_LAB_134_UNALTERED: bool = True
    CX2F_PORTAL_14_UNALTERED: bool = True
    CX2F_PORTAL_15_UNALTERED: bool = True
    CX2F_DEVICE_LAB_MANIFEST_UNALTERED: bool = True
    CX2F_NO_MERGES: bool = True
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

    def gate_shell_stack(self) -> bool:
        return bool(
            self.CX2F_NON_CLOUD_KERNEL_BOOT_PASS
            and self.CX2F_DRM_CARD_PASS
            and self.CX2F_WESTON_DRM_PASS
            and not self.CX2F_WESTON_HEADLESS_FALLBACK_USED
            and self.CX2F_GUNNCH_SHELL_RENDER_PASS
            and self.CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS
            and self.CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fail_closed_tokens(**overrides: Any) -> Cx2fTokens:
    t = Cx2fTokens()
    for k, v in overrides.items():
        if hasattr(t, k):
            setattr(t, k, v)
    return t


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2fTokens)]
