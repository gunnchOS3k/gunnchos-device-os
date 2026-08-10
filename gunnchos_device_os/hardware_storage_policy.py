"""Hardware storage policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile

MIN_GB_BY_PACK = {"cs_student_pack": 128, "game_dev_pack": 256, "research_pack": 128, "game_pack": 64}

# WP-002: packs that require Handheld expansion (microSD), not eMMC alone
HANDHELD_EXPANSION_REQUIRED_PACKS = {
    "game_pack",
    "game_dev_pack",
    "offline_essentials_pack",
}


def check_storage(device_id: str, app_pack: str = "", *, expansion_mounted: bool = True) -> dict:
    profile = load_device_profile(device_id)
    need = MIN_GB_BY_PACK.get(app_pack, 0)

    if device_id == "handheld_hybrid":
        if app_pack in HANDHELD_EXPANSION_REQUIRED_PACKS and not expansion_mounted:
            return policy_result(
                "fail",
                "Handheld MLP content requires mounted microSD expansion (WP-002 Outcome A)",
                fallback="keep_system_only",
            )
        if need and profile.storage.min_gb < need and not expansion_mounted:
            return policy_result(
                "fail",
                f"Onboard {profile.storage.min_gb}GB eMMC insufficient for {app_pack} without expansion",
                fallback="offline_essentials_pack",
            )
        if need and profile.storage.min_gb < need and expansion_mounted:
            return policy_result(
                "pass",
                f"Pack {app_pack} permitted on expansion under WP-002 Outcome A",
                fallback="",
            )
        return policy_result("pass", "Handheld system storage policy OK (Outcome A)")

    if need and profile.storage.min_gb < need:
        return policy_result("warn", f"Storage may be tight for {app_pack}", fallback="offline_essentials_pack")
    return policy_result("pass", "Storage sufficient")
