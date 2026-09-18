"""CX2G truth tokens — fail closed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2gTokens:
    CX2G_NON_CLOUD_KERNEL_SELECTED: bool = False
    CX2G_NON_CLOUD_KERNEL_BOOT_PASS: bool = False
    CX2G_VIRTIO_GPU_ENUMERATION_PASS: bool = False
    CX2G_DRM_CARD_PASS: bool = False
    CX2G_DRM_RENDER_NODE_PASS: bool = False
    CX2G_QEMU_GRAPHICS_SURFACE_PASS: bool = False
    CX2G_WESTON_DRM_PASS: bool = False
    CX2G_WESTON_HEADLESS_FALLBACK_USED: bool = False
    CX2G_WAYLAND_SOCKET_PASS: bool = False
    CX2G_DBUS_SESSION_PASS: bool = False
    CX2G_SHELL_ASSET_DELIVERY_PASS: bool = False
    CX2G_CHROMIUM_RUNTIME_PASS: bool = False
    CX2G_WAYLAND_SURFACE_PASS: bool = False
    CX2G_GUNNCH_SHELL_RENDER_PASS: bool = False
    CX2G_QEMU_FRAMEBUFFER_CAPTURE_PASS: bool = False
    CX2G_RENDER_CAPTURE_PASS: bool = False
    CX2G_REAL_SCREEN_CAPTURE_PASS: bool = False
    CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS: bool = False
    CX2G_XDG_PORTAL_SESSION_PASS: bool = False
    CX2G_REAL_HOME_WINDOW: bool = False
    CX2G_REAL_VAULT_WINDOW: bool = False
    CX2G_REAL_APP_CENTER_WINDOW: bool = False
    CX2G_REAL_CONNECT_WINDOW: bool = False
    CX2G_REAL_ASSIST_WINDOW: bool = False
    CX2G_REAL_CARE_WINDOW: bool = False
    CX2G_REAL_BROWSER_GUI_PASS: bool = False
    CX2G_REAL_APP_LIFECYCLE_GUI_PASS: bool = False
    CX2G_REAL_PRODUCTIVITY_GUI_PASS: bool = False
    CX2G_REAL_MAIL_GUI_PASS: bool = False
    CX2G_REAL_CALDAV_CARDDAV_GUI_PASS: bool = False
    CX2G_REAL_IPP_GUI_DIGITAL_PASS: bool = False
    CX2G_DIGITAL_RENDERED_A11Y_PASS: bool = False
    CX2G_REAL_OFFLINE_RECOVERY_GUI_PASS: bool = False
    CX2G_HUMAN_A11Y_PENDING: bool = True
    CX2G_PHYSICAL_PRINTER_PENDING: bool = True
    CX2G_HUMAN_AV_QUALITY_PENDING: bool = True
    CX2G_PHYSICAL_CAMERA_MIC_PENDING: bool = True
    CX2G_SINGLE_PRODUCTION_SHELL_AUTHORITY: bool = True
    CX2G_DEVICE_LAB_134_UNALTERED: bool = True
    CX2G_PORTAL_14_UNALTERED: bool = True
    CX2G_PORTAL_15_UNALTERED: bool = True
    CX2G_DEVICE_LAB_MANIFEST_UNALTERED: bool = True
    CX2G_NO_MERGES: bool = True
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
            self.CX2G_NON_CLOUD_KERNEL_BOOT_PASS
            and self.CX2G_DRM_CARD_PASS
            and self.CX2G_WESTON_DRM_PASS
            and not self.CX2G_WESTON_HEADLESS_FALLBACK_USED
            and self.CX2G_CHROMIUM_RUNTIME_PASS
            and self.CX2G_WAYLAND_SURFACE_PASS
            and self.CX2G_GUNNCH_SHELL_RENDER_PASS
            and self.CX2G_QEMU_FRAMEBUFFER_CAPTURE_PASS
            and self.CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fail_closed_tokens(**overrides: Any) -> Cx2gTokens:
    t = Cx2gTokens()
    for k, v in overrides.items():
        if hasattr(t, k):
            setattr(t, k, v)
    return t


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2gTokens)]
