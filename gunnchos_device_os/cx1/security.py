"""CX1K Security/privacy — dashboards and honest hardware discovery."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .permissions import PermissionsPlane
from .secret_store import SecretStore


@dataclass
class SecurityPrivacyPlane:
    root: Path
    permissions: PermissionsPlane
    secrets: SecretStore
    indicators: Dict[str, bool] = field(default_factory=dict)
    privacy_settings: Dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.indicators = {
            "camera_in_use": False,
            "microphone_in_use": False,
            "screen_share_in_use": False,
        }
        self.privacy_settings = {
            "telemetry": False,
            "ad_tracking": False,
            "share_diagnostics": False,
            "lock_on_sleep": True,
        }
        self._save()

    def _save(self) -> None:
        (self.root / "security_state.json").write_text(
            json.dumps(
                {
                    "indicators": self.indicators,
                    "privacy_settings": self.privacy_settings,
                },
                indent=2,
            )
            + "\n"
        )

    def set_indicator(self, name: str, active: bool) -> dict:
        if name not in self.indicators:
            raise KeyError(name)
        self.indicators[name] = active
        self._save()
        return {"indicator": name, "active": active}

    def permissions_dashboard(self) -> dict:
        return {
            "grants": self.permissions.view(),
            "portals": self.permissions.portal_probe,
            "indicators": dict(self.indicators),
        }

    def secret_storage_status(self) -> dict:
        return self.secrets.to_dict()

    def firewall_status(self) -> dict:
        ufw = shutil.which("ufw")
        pfctl = shutil.which("pfctl")
        if ufw:
            return {"available": True, "backend": "ufw", "evidence_class": "DIGITAL_PARTIAL"}
        if pfctl:
            return {"available": True, "backend": "pfctl", "evidence_class": "DIGITAL_PARTIAL"}
        return {
            "available": False,
            "evidence_class": "DIGITAL_PARTIAL",
            "notes": "firewall_tooling_absent",
        }

    def encryption_status(self) -> dict:
        # Honest: detect FileVault/LUKS presence markers without claiming enabled
        markers = {
            "fdesetup": bool(shutil.which("fdesetup")),
            "cryptsetup": bool(shutil.which("cryptsetup")),
        }
        return {
            "markers": markers,
            "disk_encryption_verified": False,
            "evidence_class": "DIGITAL_PARTIAL",
            "claim_boundary": "discovery_only_no_encryption_pass_claim",
        }

    def secure_boot_tpm_se_discovery(self) -> dict:
        mokutil = shutil.which("mokutil")
        tpm2 = shutil.which("tpm2_getcap")
        return {
            "secure_boot": {
                "tooling": bool(mokutil),
                "verified": False,
                "notes": "discovery_only",
            },
            "tpm": {
                "tooling": bool(tpm2),
                "verified": False,
                "notes": "discovery_only",
            },
            "secure_element": {
                "discovered": False,
                "verified": False,
                "notes": "no_fake_hardware_security_claims",
            },
            "evidence_class": "DIGITAL_PARTIAL",
            "claim_boundary": "discovery_only_no_hardware_security_pass",
        }

    def update_app_provenance(self, apps: List[dict]) -> dict:
        return {
            "apps": [
                {
                    "app_id": a.get("app_id"),
                    "provenance": a.get("provenance"),
                    "permissions": a.get("permissions", []),
                }
                for a in apps
            ],
            "evidence_class": "DIGITAL_PASS",
        }

    def set_privacy(self, key: str, value: bool) -> dict:
        if key not in self.privacy_settings:
            raise KeyError(key)
        self.privacy_settings[key] = value
        self._save()
        return {"key": key, "value": value}

    def diagnostics_redaction_demo(self, text: str) -> dict:
        from gunnchos_device_os.cx0.support_bundle import redact_text

        redacted = redact_text(text)
        return {
            "original_len": len(text),
            "redacted": redacted,
            "pii_removed": "example.com" not in redacted and "Bearer " not in redacted.split("[REDACTED")[0],
            "evidence_class": "DIGITAL_PASS",
        }

    def dashboard(self) -> dict:
        return {
            "permissions": self.permissions_dashboard(),
            "secret_storage": self.secret_storage_status(),
            "firewall": self.firewall_status(),
            "encryption": self.encryption_status(),
            "secure_boot_tpm_se": self.secure_boot_tpm_se_discovery(),
            "privacy_settings": dict(self.privacy_settings),
            "indicators": dict(self.indicators),
        }
