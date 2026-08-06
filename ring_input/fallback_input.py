"""Safe OS input fallback when ring auth fails or link is lost."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OsSafeFallback:
    modalities: list[str] = field(default_factory=lambda: ["keyboard", "touch", "trackpad"])
    active: bool = False
    reason: str = ""

    def engage(self, reason: str) -> dict[str, Any]:
        self.active = True
        self.reason = reason
        return {
            "fallback_active": True,
            "reason": reason,
            "modalities": list(self.modalities),
            "silent_accept": False,
            "available": len(self.modalities) > 0,
        }

    def available(self) -> bool:
        return len(self.modalities) > 0
