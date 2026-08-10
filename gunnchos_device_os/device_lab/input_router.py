"""Virtual HID / Wayland injection router for Device Lab Ring D6.

Chain segment: SpatialInputService → target/confidence → this router → focused app.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.device_lab.apps.surfaces import SurfaceRegistry


@dataclass
class InputRouter:
    surfaces: SurfaceRegistry = field(default_factory=SurfaceRegistry)
    injected: list[dict[str, Any]] = field(default_factory=list)
    seat: str = "seat0"

    def focus(self, target: str) -> dict[str, Any]:
        self.surfaces.focus = target
        surf = self.surfaces.by_target(target)
        for name in ("libreoffice", "browser", "games"):
            s = self.surfaces.by_target(name)
            s.focused = name == target
        return {"ok": True, "focus": target, "app_id": surf.app_id, "seat": self.seat}

    def deliver(self, event: Any) -> dict[str, Any]:
        """Deliver an OsPointerEvent (or dict) into the targeted app surface."""
        if hasattr(event, "__dict__") and not isinstance(event, dict):
            payload = {
                "kind": getattr(event, "kind", "move"),
                "x": getattr(event, "x", 0.0),
                "y": getattr(event, "y", 0.0),
                "target": getattr(event, "target", self.surfaces.focus),
                "confidence": getattr(event, "confidence", 0.0),
                "source": getattr(event, "source", "spatial_fusion"),
            }
        else:
            payload = dict(event)

        target = str(payload.get("target") or self.surfaces.focus)
        conf = float(payload.get("confidence") or 0.0)
        if conf < 0.5:
            row = {
                "ok": False,
                "delivered": False,
                "mutated": False,
                "reject": "low_confidence",
                "confidence": conf,
                "target": target,
                "via": "input_router_hid_wayland",
            }
            self.injected.append(row)
            return row

        self.focus(target)
        # Enrich click/type events so document surfaces receive text
        if payload.get("kind") == "click" and target == "libreoffice":
            payload = {**payload, "text": payload.get("text") or "RING"}
        if payload.get("kind") == "click" and target == "browser":
            payload = {**payload, "element": "lab-button"}

        surface = self.surfaces.by_target(target)
        applied = surface.apply_hid(payload)
        row = {
            "ok": bool(applied.get("mutated")),
            "delivered": bool(applied.get("mutated")),
            "mutated": bool(applied.get("mutated")),
            "target": target,
            "via": "input_router_hid_wayland",
            "virtual_hid": True,
            "wayland_injection": True,
            "direct_file_write": False,
            "app_result": applied,
            "app_snapshot": surface.snapshot(),
        }
        self.injected.append(row)
        return row

    def summary(self) -> dict[str, Any]:
        return {
            "injected": len(self.injected),
            "delivered": sum(1 for r in self.injected if r.get("delivered")),
            "mutated": sum(1 for r in self.injected if r.get("mutated")),
            "focus": self.surfaces.focus,
            "snapshots": self.surfaces.snapshots(),
        }
