from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class PowerPolicy:
    schema: str = "gunnchos.power_policy.v1"
    warn_pct: float = 15.0
    critical_pct: float = 5.0
    save_sync_priority_on_low: bool = True
    never_drop_user_files: bool = True

    def on_battery(self, pct: float, open_work: bool) -> dict[str, Any]:
        if pct <= self.critical_pct:
            return {
                "ok": True,
                "level": "critical",
                "warn_user": True,
                "save_sync_priority": True,
                "graceful_suspend": True,
                "data_loss": False,
                "open_work_preserved": open_work,
            }
        if pct <= self.warn_pct:
            return {
                "ok": True,
                "level": "low",
                "warn_user": True,
                "save_sync_priority": True,
                "power_shift": "efficiency",
                "data_loss": False,
            }
        return {"ok": True, "level": "normal", "warn_user": False, "data_loss": False}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "warn_pct": self.warn_pct,
            "critical_pct": self.critical_pct,
            "save_sync_priority_on_low": self.save_sync_priority_on_low,
            "never_drop_user_files": self.never_drop_user_files,
        }
