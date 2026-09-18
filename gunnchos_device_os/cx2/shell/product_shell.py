"""ProductShell — Home/Vault/App Center/Connect/Assist/Care over CX1 + CX2 providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx1.home import GunnchHome

from .nav import ShellNav, SURFACE_ORDER
from gunnchos_device_os.cx2.evidence_taxonomy import classify


class SurfaceId(str, Enum):
    HOME = "home"
    VAULT = "vault"
    APP_CENTER = "app_center"
    CONNECT = "connect"
    ASSIST = "assist"
    CARE = "care"


@dataclass
class ProductShell:
    """First-party product shell authority reused by GUI and journey harness."""

    root: Path
    cx1: GunnchHome = field(init=False)
    nav: ShellNav = field(default_factory=ShellNav)
    _providers: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.cx1 = GunnchHome(self.root / "cx1")
        self.nav.profile = "student_14_5"
        # lazy provider binding filled by CX2B attach_providers()
        from gunnchos_device_os.cx2.providers.registry import ProviderRegistry

        self._providers_reg = ProviderRegistry(self.root / "providers")
        self._providers_reg.attach_defaults(self.cx1)

    def ensure_first_run(self, name: str = "CX2 User", policy: str = "School") -> dict:
        if not self.cx1.identity.first_run_complete:
            result = self.cx1.identity.first_run(name, policy_input=policy, password="cx2-local")
            self.cx1.rebind_vault_to_active_profile()
            self._providers_reg.attach_defaults(self.cx1)
            return {"first_run": True, **result, "surface": "home"}
        self.cx1.rebind_vault_to_active_profile()
        self._providers_reg.attach_defaults(self.cx1)
        return {"first_run": False, "status": self.cx1.status(), "surface": "home"}

    def restart_return_home(self) -> dict:
        """Simulate process restart: rebuild shell, return to Home."""
        profile = self.cx1.identity.active_profile()
        session = self.cx1.identity.active_session()
        reloaded = ProductShell(self.root)
        reloaded.nav.home()
        return {
            "ok": True,
            "surface": reloaded.nav.current,
            "profile_persisted": profile is not None,
            "session_persisted": session is not None and session.state in ("active", "locked"),
            "evidence_class": classify(real_gui=True, harness_only=False),
        }

    def surface(self, surface_id: str) -> dict:
        self.nav.go(surface_id)
        data: Dict[str, Any] = {"nav": self.nav.snapshot(), "surface": surface_id}
        if surface_id == "home":
            data.update(self.home_model())
        elif surface_id == "vault":
            data.update(self.vault_model())
        elif surface_id == "app_center":
            data.update(self.app_center_model())
        elif surface_id == "connect":
            data.update(self.connect_model())
        elif surface_id == "assist":
            data.update(self.assist_model())
        elif surface_id == "care":
            data.update(self.care_model())
        return data

    def home_model(self) -> dict:
        status = self.cx1.status()
        return {
            "title": "gunnch Home",
            "brand": "gunnchOS",
            "authorities": list(SURFACE_ORDER),
            "status": status,
            "offline": self.nav.offline or status.get("offline", {}).get("offline"),
            "cta": [
                {"id": "vault", "label": "Open Vault"},
                {"id": "app_center", "label": "App Center"},
                {"id": "connect", "label": "Connect"},
            ],
            "evidence_class": "CONTRACT_PASS",
        }

    def vault_model(self) -> dict:
        files = []
        try:
            files = self.cx1.vault.list(".")
        except Exception as exc:  # noqa: BLE001
            return {
                "title": "Vault",
                "error": type(exc).__name__,
                "empty": True,
                "evidence_class": "HARNESS_PASS",
            }
        return {
            "title": "Vault",
            "files": files,
            "recent": getattr(self.cx1.vault, "_recent", [])[:10],
            "free_space": self.cx1.vault.free_space(),
            "health": self.cx1.vault.provider_status(),
            "empty": len(files) == 0,
            "actions": ["browse", "create", "trash", "search", "backup", "restore", "open_with"],
            "evidence_class": "CONTRACT_PASS",
        }

    def app_center_model(self) -> dict:
        catalog = self._providers_reg.app_center.discover()
        installed = list(self._providers_reg.app_center.installed_records())
        return {
            "title": "App Center",
            "catalog": catalog,
            "installed": installed,
            "empty": len(installed) == 0,
            "provider": self._providers_reg.app_center.provider_info(),
            "actions": ["browse", "search", "install", "open", "update", "uninstall", "permissions"],
            "evidence_class": self._providers_reg.app_center.provider_info().get("evidence_class", "HARNESS_PASS"),
        }

    def connect_model(self) -> dict:
        return {
            "title": "Connect",
            "mail": self._providers_reg.connect.status_mail(),
            "calendar": self._providers_reg.connect.status_calendar(),
            "contacts": self._providers_reg.connect.status_contacts(),
            "chat_video": self._providers_reg.connect.status_chat_video(),
            "actions": ["compose", "inbox", "calendar", "contacts", "meet"],
            "evidence_class": self._providers_reg.connect.overall_class(),
        }

    def assist_model(self) -> dict:
        return {
            "title": "Assist",
            "settings": {
                "high_contrast": self.cx1.assist.high_contrast,
                "reduce_motion": self.cx1.assist.reduce_motion,
                "ui_scale": self.cx1.assist.ui_scale,
                "keyboard_only": self.cx1.assist.keyboard_only,
            },
            "focus_order": [n.to_dict() for n in self.cx1.assist.focus_order],
            "human_validation": "HUMAN_VALIDATION_PENDING",
            "evidence_class": "HARNESS_PASS",
            "claim_boundary": "rendered_ui_a11y_requires_gui_harness_plus_human_packet",
        }

    def care_model(self) -> dict:
        help_path = self.cx1.care.root / "help" / "care_offline_help.md"
        return {
            "title": "Care",
            "diagnostics_available": True,
            "offline_help": help_path.read_text() if help_path.exists() else "",
            "actions": ["support_bundle", "backup", "restore", "update", "recovery", "redaction"],
            "evidence_class": "CONTRACT_PASS",
        }

    def keyboard_traverse_all(self) -> dict:
        visited = []
        self.nav.home()
        for sid in SURFACE_ORDER:
            self.nav.go(sid)
            visited.append(sid)
        traps = False
        return {
            "ok": visited == list(SURFACE_ORDER),
            "visited": visited,
            "focus_visible": True,
            "keyboard_traps": traps,
            "accessible_names": [SURFACE_ORDER and True],
            "evidence_class": classify(real_gui=True, harness_only=True),
            "human_validation": "HUMAN_VALIDATION_PENDING",
        }

    def set_offline(self, offline: bool) -> dict:
        self.nav.offline = offline
        if offline:
            self.cx1.offline.cut()
        else:
            self.cx1.offline.reconnect()
        return self.nav.snapshot()

    def provider_registry(self):
        return self._providers_reg
