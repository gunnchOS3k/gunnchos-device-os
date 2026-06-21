"""Theme manager — accessible visual presets."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_themes


def list_themes() -> list[str]:
    return list(load_themes().get("themes", {}).keys())


def get_theme(theme_id: str) -> dict[str, Any]:
    themes = load_themes().get("themes", {})
    if theme_id not in themes:
        raise ValueError(f"Unknown theme: {theme_id}")
    return {"id": theme_id, **themes[theme_id]}


def apply_theme(theme: dict[str, Any]) -> dict[str, Any]:
    return {
        "theme_id": theme.get("id", "default"),
        "font_scale": theme.get("font_scale", 1.0),
        "contrast_mode": theme.get("contrast_mode", "standard"),
        "color_tokens": theme.get("color_tokens", {}),
        "motion_level": theme.get("motion_level", "normal"),
        "icon_size": theme.get("icon_size", "medium"),
        "reading_density": theme.get("reading_density", "comfortable"),
        "accessibility_notes": theme.get("accessibility_notes", []),
    }
