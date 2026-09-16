"""gunnch Home — product shell wiring authorities for a profile data root."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .app_center import AppCenter
from .assist import Assist
from .browser import BrowserQualification
from .care import Care
from .connect import Connect
from .identity import IdentityPlane
from .offline import OfflinePlane
from .permissions import PermissionsPlane
from .printing import PrintingPlane
from .productivity import ProductivitySuite
from .security import SecurityPrivacyPlane
from .vault import Vault


@dataclass
class GunnchHome:
    """Product authority surface: Home / Vault / App Center / Connect / Assist / Care."""

    root: Path
    identity: IdentityPlane = field(init=False)
    vault: Vault = field(init=False)
    app_center: AppCenter = field(init=False)
    permissions: PermissionsPlane = field(init=False)
    browser: BrowserQualification = field(init=False)
    productivity: ProductivitySuite = field(init=False)
    connect: Connect = field(init=False)
    printing: PrintingPlane = field(init=False)
    assist: Assist = field(init=False)
    offline: OfflinePlane = field(init=False)
    security: SecurityPrivacyPlane = field(init=False)
    care: Care = field(init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.identity = IdentityPlane(self.root / "identity")
        # Vault binds to active profile data root when available
        vault_root = self.root / "vault"
        if self.identity.active_profile():
            vault_root = Path(self.identity.active_profile().data_root) / "vault"
        self.vault = Vault(vault_root)
        self.app_center = AppCenter(self.root / "app_center")
        self.permissions = PermissionsPlane(self.root / "permissions")
        self.browser = BrowserQualification(self.root / "browser")
        self.productivity = ProductivitySuite(self.root / "productivity", self.vault)
        self.connect = Connect(self.root / "connect", self.vault)
        self.printing = PrintingPlane(self.root / "printing")
        self.assist = Assist(self.root / "assist")
        self.offline = OfflinePlane(self.root / "offline")
        self.security = SecurityPrivacyPlane(
            self.root / "security",
            permissions=self.permissions,
            secrets=self.identity.secrets,  # type: ignore[arg-type]
        )
        self.care = Care(self.root / "care", self.vault)

    def rebind_vault_to_active_profile(self) -> Vault:
        profile = self.identity.active_profile()
        if not profile:
            raise RuntimeError("no_active_profile")
        self.vault = Vault(Path(profile.data_root) / "vault")
        self.productivity = ProductivitySuite(self.root / "productivity", self.vault)
        self.connect = Connect(self.root / "connect", self.vault)
        self.care = Care(self.root / "care", self.vault)
        return self.vault

    def entry_points(self) -> dict:
        return {
            "Home": "gunnch Home",
            "Vault": "files_sync_backup",
            "App Center": "discover_install_launch",
            "Connect": "mail_calendar_contacts_conference",
            "Assist": "accessibility",
            "Care": "support_recovery",
            "authorities": ["Home", "Vault", "App Center", "Connect", "Assist", "Care"],
        }

    def status(self) -> dict:
        session = self.identity.active_session()
        profile = self.identity.active_profile()
        return {
            "entry_points": self.entry_points(),
            "first_run_complete": self.identity.first_run_complete,
            "session": session.to_dict() if session else None,
            "profile": profile.to_dict() if profile else None,
            "offline": self.offline.status(),
            "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        }
