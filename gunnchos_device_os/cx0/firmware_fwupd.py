"""Firmware-update provider interface + fwupd/LVFS detection (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import shutil
import subprocess


@dataclass
class FirmwareUpdateProviderInventory:
    provider_id: str = "gunnchos.cx0.firmware_update_provider.v1"
    fwupd_binary_present: bool = False
    fwupdmgr_version: str | None = None
    lvfs_configured: bool = False
    devices: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "fwupd_binary_present": self.fwupd_binary_present,
            "fwupdmgr_version": self.fwupdmgr_version,
            "lvfs_configured": self.lvfs_configured,
            "devices": self.devices,
            "notes": self.notes,
            "claim_boundary": "detection_only_no_flash_no_lvfs_claim",
        }


def detect_fwupd() -> FirmwareUpdateProviderInventory:
    inv = FirmwareUpdateProviderInventory()
    path = shutil.which("fwupdmgr")
    if not path:
        inv.notes.append("fwupdmgr_absent")
        return inv
    inv.fwupd_binary_present = True
    try:
        proc = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            inv.fwupdmgr_version = (proc.stdout or proc.stderr).strip().splitlines()[0][:200]
            inv.notes.append("fwupdmgr_version_probed")
        else:
            inv.notes.append(f"fwupdmgr_version_failed_rc={proc.returncode}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        inv.notes.append(f"fwupdmgr_probe_error:{type(exc).__name__}")
    inv.lvfs_configured = False
    inv.notes.append("lvfs_not_claimed")
    return inv
