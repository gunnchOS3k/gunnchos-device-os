"""Input / uinput-style virtual HID backend."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InputBackend:
    profile: str = "touch"
    events: list[dict[str, Any]] = field(default_factory=list)

    def set_profile(self, profile: str) -> dict[str, Any]:
        self.profile = profile
        self.events.append({"kind": "profile", "profile": profile})
        return {"ok": True, "profile": profile}

    def inject(self, kind: str, **payload: Any) -> dict[str, Any]:
        ev = {"kind": kind, **payload, "via": "virtual_hid"}
        self.events.append(ev)
        return {"ok": True, "event": ev}

    def dock_desktop_profile(self) -> dict[str, Any]:
        return self.set_profile("keyboard_mouse_desktop")
