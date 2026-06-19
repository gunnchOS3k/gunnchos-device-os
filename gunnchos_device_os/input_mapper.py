"""Controller and input mapper — EVT-1 alpha."""
from __future__ import annotations

DEFAULT_BINDINGS = {
    "a": "confirm",
    "b": "back",
    "x": "action",
    "y": "menu",
    "l_stick": "navigate",
    "r_stick": "camera",
}

REMAP_PRESETS = {
    "handheld_default": DEFAULT_BINDINGS,
    "left_handed": {**DEFAULT_BINDINGS, "l_stick": "camera", "r_stick": "navigate"},
    "accessibility_large_deadzone": {**DEFAULT_BINDINGS, "deadzone": 0.25},
}


def get_bindings(preset: str = "handheld_default") -> dict:
    if preset not in REMAP_PRESETS:
        raise ValueError(preset)
    return {"preset": preset, "bindings": REMAP_PRESETS[preset], "mock": True}


def controller_first_nav_enabled(device: str) -> bool:
    return device in ("HandheldHybrid", "DSXLCoder", "WearableArenaKit")
