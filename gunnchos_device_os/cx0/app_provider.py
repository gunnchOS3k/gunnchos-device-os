"""AppProvider + sandbox/portal capability discovery (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(frozen=True)
class PortalCapability:
    name: str
    available: bool
    notes: str = ""


@dataclass
class AppProviderInventory:
    provider_id: str = "gunnchos.cx0.app_provider.v1"
    operations: List[str] = field(
        default_factory=lambda: ["discover", "install", "update", "rollback", "remove"]
    )
    lanes: List[str] = field(
        default_factory=lambda: [
            "GUNNCH_NATIVE",
            "LINUX_NATIVE",
            "FLATPAK",
            "WEB_PWA",
            "OCI_DEV",
        ]
    )
    portals: List[PortalCapability] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "operations": list(self.operations),
            "lanes": list(self.lanes),
            "portals": [
                {"name": p.name, "available": p.available, "notes": p.notes}
                for p in self.portals
            ],
            "xdg_desktop_portal_implemented": any(
                p.name == "xdg-desktop-portal" and p.available for p in self.portals
            ),
            "claim_boundary": "scaffold_only_not_product_store",
        }


def discover_portal_capabilities(probe_names: Iterable[str] | None = None) -> AppProviderInventory:
    """Return portal capability inventory.

    Does not claim xdg-desktop-portal works unless a probe marks it available.
    Default probes are digital placeholders (available=False).
    """
    names = list(probe_names or [
        "xdg-desktop-portal",
        "file-chooser",
        "screenshot",
        "screencast",
        "notifications",
        "openuri",
    ])
    portals = [
        PortalCapability(name=n, available=False, notes="not_probed_or_absent")
        for n in names
    ]
    return AppProviderInventory(portals=portals)
