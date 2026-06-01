"""Security policy stubs — secure boot / TPM targets, not certified implementation."""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class SecurityStatus:
    secure_boot: str = "target_enabled"
    tpm_present: str = "target_tpm2"
    disk_encryption: str = "target_luks_bitlocker_class"
    measured_boot: str = "planned"
    fleet_lock_capable: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def get_security_status(mode: str) -> dict:
    s = SecurityStatus()
    if mode == "school":
        s.fleet_lock_capable = True
    return s.to_dict()
