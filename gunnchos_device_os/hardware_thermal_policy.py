"""Hardware thermal policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile


def check_thermal(device_id: str, mode: str = "") -> dict:
    profile = load_device_profile(device_id)
    if mode in ("Developer", "Workshop", "Laboratory") and profile.thermal.thermal_class == "strict_throttle":
        return policy_result("fail", "Thermal class insufficient for sustained dev/research", fallback="arcade")
    return policy_result("pass", "Thermal policy acceptable", evidence_required="thermal_validation_lab")
