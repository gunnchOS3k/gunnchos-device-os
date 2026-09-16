"""Capability registry export + device-profile feature detection (CX0 scaffold)."""

from __future__ import annotations

from typing import Dict

from .accessibility_inventory import export_accessibility_inventory
from .app_provider import discover_portal_capabilities
from .continuity_provider import create_continuity_state
from .firmware_fwupd import detect_fwupd
from .peripheral_ipp import detect_print_capabilities
from .sync_backup import BackupProviderScaffold, SyncProviderScaffold


KNOWN_PROFILES = ("handheld_student", "ds_xl", "office_dock", "fleet_admin", "community_hub")


def detect_device_profile_features(device_profile: str) -> Dict:
    if device_profile not in KNOWN_PROFILES:
        raise ValueError(f"unknown_device_profile:{device_profile}")
    return {
        "device_profile": device_profile,
        "apps": discover_portal_capabilities().to_dict(),
        "peripherals": detect_print_capabilities(device_profile).to_dict(),
        "firmware": detect_fwupd().to_dict(),
        "accessibility": export_accessibility_inventory(device_profile).to_dict(),
        "continuity": create_continuity_state(f"cx0-{device_profile}").to_dict(),
        "sync": SyncProviderScaffold().to_dict(),
        "backup": {
            "provider_id": BackupProviderScaffold().provider_id,
            "destinations": BackupProviderScaffold().destinations,
            "encryption": BackupProviderScaffold().encryption,
        },
        "live_host_probing": False,
        "claim_boundary": "export_scaffold_profile_mirror_not_live_avl",
    }


def export_capability_registry(device_profile: str = "handheld_student") -> Dict:
    return {
        "schema": "gunnchos.device_os.cx0.capability_export.v1",
        "profile_features": detect_device_profile_features(device_profile),
    }
