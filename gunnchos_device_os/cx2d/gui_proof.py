"""Rendered window / AT-SPI proofs for production shell on Linux.

Fail closed: React vitest / ProductShell.surface() alone never sets CX2D_REAL_*_WINDOW.
"""

from __future__ import annotations

from typing import Any, Dict


SURFACES = ("home", "vault", "app_center", "connect", "assist", "care")


def empty_window_proofs(*, reason: str) -> Dict[str, Any]:
    return {
        "schema": "gunnchos.cx2d.gui_window_proofs.v1",
        "linux_compositor_session": False,
        "production_shell": "apps/gunnch_shell",
        "reason": reason,
        "surfaces": {
            sid: {
                "window_rendered": False,
                "keyboard_focus": False,
                "accessible_name_role": False,
                "pointer_path": False,
                "nav_back_home": False,
                "responsive_state": False,
                "empty_error_offline_state": False,
                "backend_state_displayed": False,
                "token": f"CX2D_REAL_{sid.upper()}_WINDOW",
                "value": False,
            }
            for sid in SURFACES
        },
        "tokens": {f"CX2D_REAL_{sid.upper()}_WINDOW": False for sid in SURFACES},
    }


def domain_gui_results(*, reason: str) -> Dict[str, Any]:
    """All GUI domain PASSes fail closed until Linux session + automation evidence."""
    false_domains = {
        "CX2D_REAL_BROWSER_GUI_PASS": False,
        "CX2D_REAL_APP_LIFECYCLE_GUI_PASS": False,
        "CX2D_REAL_PRODUCTIVITY_GUI_PASS": False,
        "CX2D_REAL_MAIL_GUI_PASS": False,
        "CX2D_REAL_CALDAV_CARDDAV_GUI_PASS": False,
        "CX2D_REAL_IPP_GUI_DIGITAL_PASS": False,
        "CX2D_REAL_XDG_PORTAL_PASS": False,
        "CX2D_REAL_SCREEN_CAPTURE_PASS": False,
        "CX2D_DIGITAL_RENDERED_A11Y_PASS": False,
        "CX2D_REAL_OFFLINE_RECOVERY_GUI_PASS": False,
    }
    return {
        "schema": "gunnchos.cx2d.domain_gui_results.v1",
        "reason": reason,
        "results": false_domains,
        "pending": {
            "CX2D_HUMAN_A11Y_PENDING": True,
            "CX2D_PHYSICAL_PRINTER_PENDING": True,
            "CX2D_HUMAN_AV_QUALITY_PENDING": True,
            "CX2D_PHYSICAL_CAMERA_MIC_PENDING": True,
        },
        "notes": {
            "browser": "Requires Linux GUI download/chooser/PDF — not earned",
            "app_lifecycle": "Requires Flatpak GUI via App Center — not earned",
            "productivity": "Requires LibreOffice GUI Writer/Calc/Impress — not earned",
            "ipp": "Requires CUPS/IPP print dialog GUI — not earned; physical pending",
            "portals": "Requires real D-Bus portal in session — not earned",
            "capture": "lavfi-only forbidden; compositor capture not proven",
            "a11y": "AT-SPI tree on rendered shell not proven; HUMAN_A11Y_PENDING",
            "offline": "Offline/reconnect GUI journey not proven on Linux shell",
        },
    }
