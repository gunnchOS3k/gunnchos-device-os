"""Mode switching and policy bundles."""
from __future__ import annotations

from .device_profile import MODES, get_profile

MODE_APPS: dict[str, list[str]] = {
    "school": ["WAIKE Classroom", "Ask gunnchAI3k", "Offline Library"],
    "developer": ["Code Dev Duck", "Deploy to Device", "Terminal"],
    "play": ["Arena Platform Fighter", "Media"],
    "research_measurement": ["Edge-IO Measurement", "7GC Digital Twin", "AI-RAN Lab"],
    "fleet_admin": ["Fleet Dashboard", "Policy Sync"],
}


def switch_mode(device: str, mode: str) -> dict:
    profile = get_profile(device, mode)
    return {
        "profile": profile,
        "allowed_apps": MODE_APPS.get(mode, []),
        "qos_preset": "urllc_strict" if mode == "play" else "balanced",
    }


def validate_mode(mode: str) -> bool:
    return mode in MODES
