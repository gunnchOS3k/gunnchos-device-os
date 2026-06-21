"""Hardware storage policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile

MIN_GB_BY_PACK = {"cs_student_pack": 128, "game_dev_pack": 256, "research_pack": 128}


def check_storage(device_id: str, app_pack: str = "") -> dict:
    profile = load_device_profile(device_id)
    need = MIN_GB_BY_PACK.get(app_pack, 0)
    if need and profile.storage.min_gb < need:
        return policy_result("warn", f"Storage may be tight for {app_pack}", fallback="offline_essentials_pack")
    return policy_result("pass", "Storage sufficient")
