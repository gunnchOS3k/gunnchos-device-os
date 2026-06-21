"""Journey preset engine — data-driven scooter-to-spaceship modes."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_accessibility_defaults, load_journey_presets


def list_presets() -> list[str]:
    return list(load_journey_presets().get("presets", {}).keys())


def get_preset(preset_id: str) -> dict[str, Any]:
    presets = load_journey_presets().get("presets", {})
    if preset_id not in presets:
        raise ValueError(f"Unknown journey preset: {preset_id}")
    preset = presets[preset_id]
    a11y = load_accessibility_defaults().get("presets", {}).get(preset_id, {})
    return {
        "id": preset_id,
        **preset,
        "accessibility_defaults": a11y,
    }


def get_exit_paths(preset_id: str) -> list[str]:
    preset = get_preset(preset_id)
    return preset.get("exit_paths", [])
