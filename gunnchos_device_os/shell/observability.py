"""Wave 002 shell observability hooks (section 23)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.identity import utc_now_iso


@dataclass
class ShellObservability:
    events: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, component: str, action: str, **details: Any) -> dict[str, Any]:
        row = {"ts": utc_now_iso(), "component": component, "action": action, **details}
        self.events.append(row)
        return row

    def metrics(self) -> dict[str, Any]:
        by_component: dict[str, int] = {}
        for ev in self.events:
            c = ev["component"]
            by_component[c] = by_component.get(c, 0) + 1
        return {"total_events": len(self.events), "by_component": by_component}

    def trace_tail(self, n: int = 20) -> list[dict[str, Any]]:
        return list(self.events[-n:])
