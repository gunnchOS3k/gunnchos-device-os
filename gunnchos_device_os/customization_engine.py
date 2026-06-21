"""Customization engine — theme, layout, and profile import/export."""
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from .theme_manager import apply_theme, get_theme, list_themes
from .user_profile_schema import UserProfile


class CustomizationEngine:
    def __init__(self, profile: UserProfile) -> None:
        self.profile = profile
        self._pinned_apps: list[str] = []
        self._widgets: list[str] = []
        self._theme_id = "default"
        self._settings_view = profile.customization_depth

    def change_theme(self, theme_id: str) -> dict[str, Any]:
        theme = get_theme(theme_id)
        self._theme_id = theme_id
        return apply_theme(theme)

    def change_font_scale(self, scale: float) -> dict[str, Any]:
        theme = apply_theme(get_theme(self._theme_id))
        theme["font_scale"] = scale
        return theme

    def change_contrast(self, mode: str) -> dict[str, Any]:
        theme = apply_theme(get_theme(self._theme_id))
        theme["contrast_mode"] = mode
        return theme

    def change_home_layout(self, layout: str) -> dict[str, Any]:
        return {"layout": layout, "profile": self.profile.user_id}

    def pin_app(self, app_id: str) -> list[str]:
        if app_id not in self._pinned_apps:
            self._pinned_apps.append(app_id)
        return list(self._pinned_apps)

    def unpin_app(self, app_id: str) -> list[str]:
        self._pinned_apps = [a for a in self._pinned_apps if a != app_id]
        return list(self._pinned_apps)

    def choose_widgets(self, widgets: list[str]) -> list[str]:
        self._widgets = list(widgets)
        return list(self._widgets)

    def set_input_method(self, method: str) -> UserProfile:
        prefs = list(self.profile.input_preferences)
        if method not in prefs:
            prefs.append(method)
        self.profile.input_preferences = prefs
        return self.profile

    def set_settings_view(self, depth: str) -> str:
        self._settings_view = depth  # type: ignore[assignment]
        self.profile.customization_depth = depth  # type: ignore[assignment]
        return depth

    def export_profile(self) -> str:
        payload = {
            "profile": self.profile.to_dict(),
            "pinned_apps": self._pinned_apps,
            "widgets": self._widgets,
            "theme_id": self._theme_id,
            "settings_view": self._settings_view,
            "available_themes": list_themes(),
        }
        return json.dumps(payload, indent=2)

    def import_profile(self, data: str) -> UserProfile:
        payload = json.loads(data)
        self.profile = UserProfile.from_dict(payload["profile"])
        self._pinned_apps = payload.get("pinned_apps", [])
        self._widgets = payload.get("widgets", [])
        self._theme_id = payload.get("theme_id", "default")
        self._settings_view = payload.get("settings_view", "simple")
        return self.profile

    def reset_to_safe_defaults(self) -> dict[str, Any]:
        safe = deepcopy(self.profile)
        safe.customization_depth = "simple"
        safe.privacy_level = "standard"
        self.profile = safe
        self._pinned_apps = []
        self._widgets = []
        self._theme_id = "default"
        self._settings_view = "simple"
        return {
            "profile": self.profile.to_dict(),
            "theme": apply_theme(get_theme("default")),
            "message": "Reset to safe defaults",
        }
