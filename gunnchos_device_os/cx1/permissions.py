"""CX1D Permissions + XDG Desktop Portal probes — fail closed if absent."""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


PORTAL_NAMES = (
    "xdg-desktop-portal",
    "file-chooser",
    "camera",
    "microphone",
    "screencast",
    "openuri",
    "notifications",
    "settings",
)

PERMISSION_STATES = ("grant", "deny", "ask", "revoke")


@dataclass
class PermissionRecord:
    subject: str
    capability: str
    state: str
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "schema": "gunnchos.contracts.PermissionGrant.v1",
            "subject": self.subject,
            "capability": self.capability,
            "state": self.state,
            "updated_at": self.updated_at,
        }


@dataclass
class PermissionsPlane:
    root: Path
    grants: Dict[str, PermissionRecord] = field(default_factory=dict)
    portal_probe: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.probe_portals()
        self._load()

    def _key(self, subject: str, capability: str) -> str:
        return f"{subject}::{capability}"

    def _load(self) -> None:
        path = self.root / "grants.json"
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for raw in data.get("grants", []):
            rec = PermissionRecord(
                subject=raw["subject"],
                capability=raw["capability"],
                state=raw["state"],
                updated_at=raw.get("updated_at", time.time()),
            )
            self.grants[self._key(rec.subject, rec.capability)] = rec

    def save(self) -> None:
        (self.root / "grants.json").write_text(
            json.dumps({"grants": [g.to_dict() for g in self.grants.values()]}, indent=2) + "\n"
        )

    def probe_portals(self) -> Dict[str, dict]:
        """Honest availability probe — fail closed when tooling absent."""
        xdg = shutil.which("xdg-desktop-portal") or shutil.which("xdg-desktop-portal-gtk")
        # On macOS CI there is typically no xdg portal; mark unavailable.
        results = {}
        for name in PORTAL_NAMES:
            available = False
            notes = "not_probed_or_absent"
            if name == "xdg-desktop-portal":
                available = bool(xdg)
                notes = f"binary={xdg}" if xdg else "xdg_desktop_portal_absent"
            elif name == "file-chooser":
                # Digital file chooser always available via Vault adapter
                available = True
                notes = "vault_file_chooser_adapter"
            elif name in ("notifications", "openuri", "settings"):
                available = True
                notes = "digital_adapter_available"
            elif name in ("camera", "microphone", "screencast"):
                available = False
                notes = "hardware_or_portal_absent_fail_closed"
            results[name] = {"name": name, "available": available, "notes": notes}
        self.portal_probe = results
        (self.root / "portal_probe.json").write_text(json.dumps(results, indent=2) + "\n")
        return results

    def set_permission(self, subject: str, capability: str, state: str) -> PermissionRecord:
        if state not in PERMISSION_STATES:
            raise ValueError(f"state_invalid:{state}")
        # fail closed if portal capability absent and state is grant
        portal = self.portal_probe.get(capability) or self.portal_probe.get(
            capability.replace(".", "-")
        )
        if state == "grant" and portal and not portal.get("available"):
            raise PermissionError(f"portal_absent_fail_closed:{capability}")
        rec = PermissionRecord(subject=subject, capability=capability, state=state)
        self.grants[self._key(subject, capability)] = rec
        self.save()
        return rec

    def revoke(self, subject: str, capability: str) -> PermissionRecord:
        return self.set_permission(subject, capability, "revoke")

    def view(self, subject: Optional[str] = None) -> List[dict]:
        out = [g.to_dict() for g in self.grants.values()]
        if subject:
            out = [g for g in out if g["subject"] == subject]
        return out

    def check(self, subject: str, capability: str) -> str:
        rec = self.grants.get(self._key(subject, capability))
        if not rec:
            return "ask"
        if rec.state == "revoke":
            return "deny"
        return rec.state

    def file_chooser(self, *, allow: bool = True) -> dict:
        portal = self.portal_probe["file-chooser"]
        if not portal["available"]:
            return {"ok": False, "reason": "file_chooser_absent", "fail_closed": True}
        if not allow:
            return {"ok": False, "reason": "user_denied", "fail_closed": True}
        return {"ok": True, "adapter": "vault_file_chooser", "evidence_class": "DIGITAL_PASS"}

    def open_uri(self, uri: str) -> dict:
        if not self.portal_probe["openuri"]["available"]:
            return {"ok": False, "reason": "openuri_absent", "fail_closed": True}
        return {"ok": True, "uri": uri, "adapter": "digital_openuri"}

    def notify(self, title: str, body: str) -> dict:
        if not self.portal_probe["notifications"]["available"]:
            return {"ok": False, "fail_closed": True}
        path = self.root / "notifications.log"
        with path.open("a") as fh:
            fh.write(json.dumps({"title": title, "body": body, "ts": time.time()}) + "\n")
        return {"ok": True, "title": title}

    def settings_query(self, key: str) -> dict:
        if not self.portal_probe["settings"]["available"]:
            return {"ok": False, "fail_closed": True}
        defaults = {"theme": "system", "locale": "en-US", "reduce_motion": False}
        return {"ok": True, "key": key, "value": defaults.get(key)}
