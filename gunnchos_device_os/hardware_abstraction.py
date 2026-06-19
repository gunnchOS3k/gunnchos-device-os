"""Hardware abstraction — device profile definitions."""
from __future__ import annotations

DEVICE_PROFILES: dict[str, dict] = {
    "Student14": {
        "displays": 1, "controllers": False, "keyboard": True, "battery": "large",
        "dock": True, "thermal": "laptop", "storage": "nvme_512gb_min", "ram_gb": 16,
        "modes": ["School", "Developer", "Play", "Media", "Research Measurement", "Admin"],
    },
    "HandheldHybrid": {
        "displays": 1, "controllers": True, "keyboard": False, "battery": "handheld",
        "dock": True, "thermal": "handheld", "storage": "nvme_512gb_min", "ram_gb": 16,
        "modes": ["School", "Developer", "Play", "Media"],
    },
    "DSXLCoder": {
        "displays": 2, "controllers": True, "keyboard": "optional_snap", "battery": "clamshell",
        "dock": False, "thermal": "passive_preferred", "storage": "emmc_or_nvme_256gb_min", "ram_gb": 8,
        "modes": ["School", "Developer"],
    },
    "WearableArenaKit": {
        "displays": 0, "controllers": True, "keyboard": False, "battery": "wearable",
        "dock": "charging_case", "thermal": "wearable", "storage": "flash", "ram_gb": 1,
        "modes": ["Play"],
    },
}


def get_device_profile(name: str) -> dict:
    if name not in DEVICE_PROFILES:
        raise ValueError(f"Unknown device: {name}")
    return {"device": name, **DEVICE_PROFILES[name]}
