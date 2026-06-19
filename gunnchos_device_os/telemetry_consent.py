"""Mock telemetry consent — opt-in only."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConsentState:
    opted_in: bool = False
    aggregated_only: bool = True
    local_buffer: list[dict[str, Any]] = field(default_factory=list)

    def record(self, metric: str, value: Any) -> None:
        if not self.opted_in:
            return
        self.local_buffer.append({"metric": metric, "value": value, "aggregated": True})

    def export(self) -> dict:
        return {"opted_in": self.opted_in, "events": len(self.local_buffer), "aggregated_only": self.aggregated_only}

    def delete_all(self) -> None:
        self.local_buffer.clear()
