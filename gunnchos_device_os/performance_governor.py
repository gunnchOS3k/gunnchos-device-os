"""Performance governor profiles."""
from __future__ import annotations

PROFILES = {
    "school": {"cpu_cap_percent": 70, "gpu_cap_percent": 50},
    "battery_saver": {"cpu_cap_percent": 50, "gpu_cap_percent": 30},
    "balanced": {"cpu_cap_percent": 85, "gpu_cap_percent": 70},
    "gaming": {"cpu_cap_percent": 100, "gpu_cap_percent": 100},
    "docked_performance": {"cpu_cap_percent": 100, "gpu_cap_percent": 100, "tdp_boost": True},
    "thermal_emergency": {"cpu_cap_percent": 40, "gpu_cap_percent": 20, "fan_max": True},
}


def get_performance_profile(name: str) -> dict:
    if name not in PROFILES:
        raise ValueError(name)
    return {"profile": name, **PROFILES[name]}
