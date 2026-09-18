"""Device profile matrix for CX2 — product vs provider booleans separated."""

from __future__ import annotations

PROFILES = {
    "student_14_5": {
        "display": "14.5-inch student",
        "input": ["keyboard", "trackpad", "touch"],
        "shell_layout": "laptop",
        "product": {
            "home": True,
            "vault": True,
            "app_center": True,
            "connect": True,
            "assist": True,
            "care": True,
        },
        "provider": {
            "browser_gui": False,
            "libreoffice_cli": True,
            "flatpak": False,
            "cups": False,
            "portals": False,
        },
        "edge_io_rings": "accessory_not_desktop",
    },
    "handheld_hybrid": {
        "display": "handheld hybrid",
        "input": ["touch", "gamepad", "rings"],
        "shell_layout": "handheld",
        "product": {
            "home": True,
            "vault": True,
            "app_center": True,
            "connect": True,
            "assist": True,
            "care": True,
        },
        "provider": {
            "browser_gui": False,
            "libreoffice_cli": True,
            "flatpak": False,
            "cups": False,
            "portals": False,
        },
        "edge_io_rings": "accessory_not_desktop",
    },
    "ds_xl": {
        "display": "DS-XL dual",
        "input": ["keyboard", "mouse", "touch"],
        "shell_layout": "ds_xl",
        "product": {
            "home": True,
            "vault": True,
            "app_center": True,
            "connect": True,
            "assist": True,
            "care": True,
        },
        "provider": {
            "browser_gui": False,
            "libreoffice_cli": True,
            "flatpak": False,
            "cups": False,
            "portals": False,
        },
        "edge_io_rings": "accessory_not_desktop",
    },
    "docked": {
        "display": "docked external",
        "input": ["keyboard", "mouse"],
        "shell_layout": "docked",
        "product": {
            "home": True,
            "vault": True,
            "app_center": True,
            "connect": True,
            "assist": True,
            "care": True,
        },
        "provider": {
            "browser_gui": False,
            "libreoffice_cli": True,
            "flatpak": False,
            "cups": False,
            "portals": False,
        },
        "edge_io_rings": "accessory_not_desktop",
    },
    "ci_qemu": {
        "display": "CI/QEMU headless",
        "input": ["virtual"],
        "shell_layout": "ci",
        "product": {
            "home": True,
            "vault": True,
            "app_center": True,
            "connect": True,
            "assist": True,
            "care": True,
        },
        "provider": {
            "browser_gui": False,
            "libreoffice_cli": True,
            "flatpak": False,
            "cups": False,
            "portals": False,
        },
        "edge_io_rings": "accessory_not_desktop",
    },
}


def matrix_document() -> dict:
    return {
        "schema": "gunnchos.cx2.device_profile_matrix.v1",
        "matrix": PROFILES,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "claim_boundary": "product_surface_booleans_separate_from_provider_booleans",
    }
