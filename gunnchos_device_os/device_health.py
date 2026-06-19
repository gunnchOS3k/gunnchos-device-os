"""Device health dashboard — EVT-1 alpha mock metrics."""
from __future__ import annotations


def get_health_snapshot(device: str) -> dict:
    return {
        "device": device,
        "battery_percent": 78,
        "thermal_celsius": 42,
        "storage_free_gb": 312,
        "ram_available_gb": 9.2,
        "wifi_signal": "good",
        "last_update_check": "mock",
        "secure_boot": "design_target_not_verified",
        "tpm": "design_target_not_verified",
        "mock": True,
    }
