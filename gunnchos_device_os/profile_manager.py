"""User profile manager — EVT-1 alpha."""
from __future__ import annotations

PROFILES = (
    "student", "parent_guardian", "educator", "developer",
    "admin", "research_operator", "guest", "community_partner",
)

PROFILE_DEFAULTS: dict[str, dict] = {
    "student": {"default_mode": "School", "can_switch_to": ["School", "Play", "Media"]},
    "parent_guardian": {"default_mode": "School", "can_switch_to": ["School", "Admin"]},
    "educator": {"default_mode": "School", "can_switch_to": ["School", "Developer", "Admin"]},
    "developer": {"default_mode": "Developer", "can_switch_to": ["Developer", "Play", "Media"]},
    "admin": {"default_mode": "Admin", "can_switch_to": list(__import__("gunnchos_device_os.mode_manager", fromlist=["MODES"]).MODES)},
    "research_operator": {"default_mode": "Research Measurement", "can_switch_to": ["Research Measurement", "Developer"]},
    "guest": {"default_mode": "School", "can_switch_to": ["School"]},
    "community_partner": {"default_mode": "School", "can_switch_to": ["School", "Admin", "Research Measurement"]},
}


def get_profile(name: str) -> dict:
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}")
    return {"profile": name, **PROFILE_DEFAULTS[name]}
