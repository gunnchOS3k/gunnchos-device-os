"""Hardware display policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile


def check_display(device_id: str, workspace: str = "") -> dict:
    profile = load_device_profile(device_id)
    if workspace in ("essay_studio", "coding_lab") and profile.display.size_inches and profile.display.size_inches < 10:
        return policy_result("warn", "Small display — long-form work may need dock/external display", fallback="dock")
    return policy_result("pass", "Display sufficient for workspace")
