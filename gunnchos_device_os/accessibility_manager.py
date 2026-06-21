"""Accessibility manager — inclusive input and display settings."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_accessibility_defaults


SUPPORTED_FEATURES = (
    "keyboard_navigation", "controller_navigation", "touch_navigation",
    "screen_reader_labels", "captions_preference", "reduced_motion",
    "high_contrast", "large_text", "simplified_language", "focus_mode",
    "color_safe_mode", "audio_cues", "haptic_cues", "one_hand_mode",
    "switch_access", "voice_input",
)


def get_defaults(preset_id: str = "default") -> dict[str, Any]:
    presets = load_accessibility_defaults().get("presets", {})
    base = load_accessibility_defaults().get("global", {})
    merged = {**base, **presets.get(preset_id, {})}
    return merged


def apply_settings(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = get_defaults()
    if overrides:
        settings.update(overrides)
    return settings


def validate_coverage(settings: dict[str, Any]) -> list[str]:
    missing = [f for f in SUPPORTED_FEATURES if f not in settings]
    return missing
