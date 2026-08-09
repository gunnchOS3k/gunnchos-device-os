from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NotificationPolicy:
    schema: str = "gunnchos.notification_policy.v1"
    rate_limit_per_min: int = 20
    focus_mode_blocks: tuple[str, ...] = ("game", "social", "promo")
    focus_mode_allows: tuple[str, ...] = ("accessibility", "emergency", "admin", "timer")
    destroy_media_forbidden: bool = True
    _inbox: list[dict[str, Any]] = field(default_factory=list)
    focus_mode: bool = False

    def set_focus_mode(self, enabled: bool) -> dict[str, Any]:
        self.focus_mode = enabled
        return {"ok": True, "focus_mode": enabled}

    def push(self, category: str, title: str) -> dict[str, Any]:
        if self.focus_mode and category in self.focus_mode_blocks:
            return {
                "ok": True,
                "delivered": False,
                "blocked_by_focus": True,
                "category": category,
            }
        item = {"category": category, "title": title}
        self._inbox.append(item)
        return {"ok": True, "delivered": True, "item": item, "media_destroyed": False}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "rate_limit_per_min": self.rate_limit_per_min,
            "focus_mode_blocks": list(self.focus_mode_blocks),
            "focus_mode_allows": list(self.focus_mode_allows),
            "destroy_media_forbidden": self.destroy_media_forbidden,
        }
