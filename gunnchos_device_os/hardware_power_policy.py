"""Hardware power policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile


def check_power(device_id: str, mode: str = "") -> dict:
    profile = load_device_profile(device_id)
    if mode in ("Play", "Arcade", "Media") and profile.power.battery_class == "wearable_short_cycle":
        return policy_result("warn", "Limited battery — venue power recommended", evidence_required="battery_validation_lab")
    return policy_result("pass", "Power profile acceptable", evidence_required="battery_validation_lab")
