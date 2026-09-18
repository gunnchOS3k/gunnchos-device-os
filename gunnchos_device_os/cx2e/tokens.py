"""CX2E truth tokens — fail closed unless guest graphical proof is earned."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict


@dataclass
class Cx2eTokens:
    # Session foundation
    CX2E_QEMU_GUEST_BOOT_PASS: bool = False
    CX2E_GUEST_LINUX_PROVEN: bool = False
    CX2E_WESTON_SESSION_PASS: bool = False
    CX2E_WAYLAND_SOCKET_PASS: bool = False
    CX2E_DBUS_SESSION_PASS: bool = False
    CX2E_XDG_PORTAL_SESSION_PASS: bool = False
    CX2E_GUNNCH_SHELL_RENDER_PASS: bool = False
    CX2E_REAL_INPUT_PATH_PASS: bool = False
    CX2E_RENDER_CAPTURE_PASS: bool = False
    CX2E_REAL_SCREEN_CAPTURE_PASS: bool = False
    # Surfaces
    CX2E_REAL_HOME_WINDOW: bool = False
    CX2E_REAL_VAULT_WINDOW: bool = False
    CX2E_REAL_APP_CENTER_WINDOW: bool = False
    CX2E_REAL_CONNECT_WINDOW: bool = False
    CX2E_REAL_ASSIST_WINDOW: bool = False
    CX2E_REAL_CARE_WINDOW: bool = False
    # Provider GUI
    CX2E_REAL_BROWSER_GUI_PASS: bool = False
    CX2E_REAL_APP_LIFECYCLE_GUI_PASS: bool = False
    CX2E_REAL_PRODUCTIVITY_GUI_PASS: bool = False
    CX2E_REAL_MAIL_GUI_PASS: bool = False
    CX2E_REAL_CALDAV_CARDDAV_GUI_PASS: bool = False
    CX2E_REAL_IPP_GUI_DIGITAL_PASS: bool = False
    CX2E_REAL_CHAT_VIDEO_GUI_ATTEMPT: bool = False
    CX2E_DIGITAL_RENDERED_A11Y_PASS: bool = False
    CX2E_REAL_OFFLINE_RECOVERY_GUI_PASS: bool = False
    # Authority / firewall
    CX2E_SINGLE_PRODUCTION_SHELL_AUTHORITY: bool = True
    CX2E_HUMAN_A11Y_PENDING: bool = True
    CX2E_PHYSICAL_PRINTER_PENDING: bool = True
    CX2E_HUMAN_AV_QUALITY_PENDING: bool = True
    CX2E_PHYSICAL_CAMERA_MIC_PENDING: bool = True
    CX2E_DEVICE_LAB_134_UNALTERED: bool = True
    CX2E_PORTAL_14_UNALTERED: bool = True
    CX2E_PORTAL_15_UNALTERED: bool = True
    CX2E_DEVICE_LAB_MANIFEST_UNALTERED: bool = True
    CX2E_NO_MERGES: bool = True
    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    # Composite truth (guest facts only)
    guest_booted: bool = False
    guest_is_linux: bool = False
    compositor_running: bool = False
    wayland_socket_alive: bool = False
    shell_window_rendered: bool = False
    lab_blocker: str = ""
    notes: str = ""

    def graphical_truth(self) -> bool:
        return bool(
            self.guest_booted
            and self.guest_is_linux
            and self.compositor_running
            and self.wayland_socket_alive
            and self.shell_window_rendered
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fail_closed_tokens(*, lab_blocker: str = "", **overrides: Any) -> Cx2eTokens:
    t = Cx2eTokens(lab_blocker=lab_blocker)
    for k, v in overrides.items():
        if hasattr(t, k):
            setattr(t, k, v)
    return t


def apply_session_facts(t: Cx2eTokens, facts: Dict[str, Any]) -> Cx2eTokens:
    """Map guest session facts onto tokens. Never uses host platform."""
    t.guest_booted = bool(facts.get("guest_booted"))
    t.guest_is_linux = bool(facts.get("guest_is_linux"))
    t.compositor_running = bool(facts.get("compositor_running"))
    t.wayland_socket_alive = bool(facts.get("wayland_socket_alive"))
    t.shell_window_rendered = bool(facts.get("shell_window_rendered"))
    t.CX2E_QEMU_GUEST_BOOT_PASS = t.guest_booted
    t.CX2E_GUEST_LINUX_PROVEN = t.guest_is_linux
    t.CX2E_WESTON_SESSION_PASS = t.compositor_running
    t.CX2E_WAYLAND_SOCKET_PASS = t.wayland_socket_alive
    t.CX2E_DBUS_SESSION_PASS = bool(facts.get("dbus_session_alive"))
    t.CX2E_XDG_PORTAL_SESSION_PASS = bool(facts.get("xdg_portal_pass"))
    t.CX2E_GUNNCH_SHELL_RENDER_PASS = t.shell_window_rendered
    t.CX2E_REAL_INPUT_PATH_PASS = bool(facts.get("real_input_pass"))
    t.CX2E_RENDER_CAPTURE_PASS = bool(facts.get("render_capture_pass"))
    t.CX2E_REAL_SCREEN_CAPTURE_PASS = bool(facts.get("real_screen_capture_pass"))
    for surf in ("HOME", "VAULT", "APP_CENTER", "CONNECT", "ASSIST", "CARE"):
        key = f"CX2E_REAL_{surf}_WINDOW"
        setattr(t, key, bool(facts.get(key.lower()) or facts.get(f"surface_{surf.lower()}")))
    for dom in (
        "BROWSER_GUI",
        "APP_LIFECYCLE_GUI",
        "PRODUCTIVITY_GUI",
        "MAIL_GUI",
        "CALDAV_CARDDAV_GUI",
        "IPP_GUI_DIGITAL",
        "OFFLINE_RECOVERY_GUI",
    ):
        attr = f"CX2E_REAL_{dom}_PASS"
        setattr(t, attr, bool(facts.get(attr) or facts.get(dom.lower())))
    t.CX2E_REAL_CHAT_VIDEO_GUI_ATTEMPT = bool(facts.get("chat_video_attempt"))
    t.CX2E_DIGITAL_RENDERED_A11Y_PASS = bool(facts.get("digital_a11y_pass"))
    if facts.get("lab_blocker"):
        t.lab_blocker = str(facts["lab_blocker"])
    return t


TOKEN_FIELD_NAMES = [f.name for f in fields(Cx2eTokens)]
