"""Hardware accessibility policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile


def check_accessibility(device_id: str, needs: list[str] | None = None) -> dict:
    profile = load_device_profile(device_id)
    needs = needs or []
    if "controller_navigation" in needs and not profile.accessibility.controller_navigation and not profile.input.controller:
        return policy_result("warn", "Controller navigation limited — touch/keyboard fallback", fallback="touch")
    return policy_result("pass", "Accessibility defaults available", evidence_required="accessibility_uat_required")
