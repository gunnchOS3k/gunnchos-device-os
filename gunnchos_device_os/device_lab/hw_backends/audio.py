"""Audio backend — dock audio route lifecycle (PipeWire/ALSA when present)."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Any


@dataclass
class AudioBackend:
    route: str = "internal"
    devices: list[str] | None = None

    def start(self) -> dict[str, Any]:
        pw = shutil.which("pw-cli") or shutil.which("pipewire")
        alsa = shutil.which("aplay")
        self.devices = ["internal"]
        self.route = "internal"
        return {
            "ok": True,
            "route": self.route,
            "pipewire": bool(pw),
            "alsa": bool(alsa),
            "backend": "pipewire_or_logical_loopback",
        }

    def dock_attach(self) -> dict[str, Any]:
        self.route = "dock"
        if self.devices is None:
            self.devices = []
        if "dock" not in self.devices:
            self.devices.append("dock")
        return {"ok": True, "route": self.route, "devices": list(self.devices)}

    def dock_detach(self) -> dict[str, Any]:
        self.route = "internal"
        if self.devices and "dock" in self.devices:
            self.devices.remove("dock")
        return {"ok": True, "route": self.route, "devices": list(self.devices or [])}
