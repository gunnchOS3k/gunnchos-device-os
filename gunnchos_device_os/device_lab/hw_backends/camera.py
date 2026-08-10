"""Camera stub / v4l2loopback when available."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Any


@dataclass
class CameraBackend:
    enabled: bool = False

    def start(self) -> dict[str, Any]:
        v4l = shutil.which("v4l2-ctl")
        self.enabled = False  # stub unless explicitly needed
        return {
            "ok": True,
            "enabled": self.enabled,
            "v4l2": bool(v4l),
            "mode": "stub_available",
            "note": "Camera stub only unless journey requires synthetic capture",
        }
