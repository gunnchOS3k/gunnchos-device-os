"""Hardware network policy."""
from __future__ import annotations

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile


def check_network(device_id: str, offline_first: bool = False) -> dict:
    profile = load_device_profile(device_id)
    if offline_first and not profile.network.offline_capable:
        return policy_result("warn", "Offline-first requested — verify cached content")
    return policy_result("pass", "Network/offline policy OK")
