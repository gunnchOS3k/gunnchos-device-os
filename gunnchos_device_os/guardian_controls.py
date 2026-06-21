"""Guardian controls — mock family safety and supervision."""
from __future__ import annotations

from typing import Any


AGE_BAND_DEFAULTS: dict[str, dict[str, Any]] = {
    "pre_k": {"screen_time_minutes": 30, "content_filter": "strict", "app_approval": True},
    "elementary": {"screen_time_minutes": 60, "content_filter": "strict", "app_approval": True},
    "middle_school": {"screen_time_minutes": 90, "content_filter": "moderate", "app_approval": True},
    "high_school": {"screen_time_minutes": 120, "content_filter": "moderate", "app_approval": False},
    "undergraduate": {"screen_time_minutes": None, "content_filter": "light", "app_approval": False},
    "graduate": {"screen_time_minutes": None, "content_filter": "light", "app_approval": False},
    "postdoc": {"screen_time_minutes": None, "content_filter": "light", "app_approval": False},
    "adult": {"screen_time_minutes": None, "content_filter": "light", "app_approval": False},
    "senior": {"screen_time_minutes": None, "content_filter": "light", "app_approval": False},
}


def apply_guardian_defaults(age_band: str) -> dict[str, Any]:
    defaults = AGE_BAND_DEFAULTS.get(age_band, AGE_BAND_DEFAULTS["elementary"])
    return {
        "age_band": age_band,
        "school_mode_restrictions": True,
        "play_time_window": {"start": "15:00", "end": "19:00"},
        "media_content_caution": defaults["content_filter"],
        "app_approval_list": defaults["app_approval"],
        "privacy_safe_telemetry": True,
        "private_content_inspection": False,
        "emergency_unlock_path": "guardian_pin_or_biometric",
        "audit_log": "placeholder",
        **defaults,
        "mock": True,
    }


def enable_guardian_controls(profile_id: str, age_band: str) -> dict[str, Any]:
    return {
        "profile_id": profile_id,
        "enabled": True,
        "controls": apply_guardian_defaults(age_band),
        "mock": True,
    }
