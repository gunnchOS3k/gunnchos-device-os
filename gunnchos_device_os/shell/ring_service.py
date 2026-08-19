"""Ring input service — anti-replay chain integration (Wave 002 / OS-PLATFORM-004)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ring_input import RingInputAdapter


@dataclass
class RingInputService:
    """OS-facing ring service wrapping the authenticated adapter + input router hook."""

    host_id: str = "wave002-host"
    adapter: RingInputAdapter = field(default_factory=lambda: RingInputAdapter(host_id="wave002-host"))
    routed: list[dict[str, Any]] = field(default_factory=list)

    def attach_session(self, session_material: dict[str, Any], calibration_registry: Any) -> None:
        self.adapter.attach_session(session_material, calibration_registry)

    def ingest(self, event: dict[str, Any], *, now_ms: int | None = None) -> dict[str, Any]:
        action = self.adapter.ingest(event, now_ms=now_ms)
        if action is None:
            return {
                "accepted": False,
                "reason": self.adapter.fallback.reason or "rejected",
                "fallback_active": self.adapter.fallback.active,
            }
        row = {
            "accepted": True,
            "kind": action.kind,
            "event_type": action.event_type,
            "device_id": action.device_id,
            "session_id": action.session_id,
            "confidence": action.confidence,
            "authenticated": action.authenticated,
        }
        self.routed.append(row)
        return row

    def route_to_input(self, input_router: Any, *, target: str = "libreoffice") -> dict[str, Any]:
        """Deliver last accepted ring action through normalized input router."""
        if not self.adapter.actions:
            return {"ok": False, "reason": "no_actions"}
        last = self.adapter.actions[-1]
        payload = {
            "kind": "move" if last.kind == "pointer_delta" else "click",
            "target": target,
            "confidence": last.confidence,
            "source": "ring",
            "dx": last.payload.get("dx", 0),
            "dy": last.payload.get("dy", 0),
        }
        if hasattr(input_router, "deliver"):
            return input_router.deliver(payload)
        return {"ok": False, "reason": "router_missing_deliver"}

    def revoke_device(self, device_id: str) -> None:
        self.adapter.receiver.revocation.revoke_device(device_id)

    def status(self) -> dict[str, Any]:
        base = self.adapter.status()
        base["service"] = "gunnchos_device_os.shell.ring_service"
        base["routed_events"] = len(self.routed)
        base["PHYSICAL_RING_CLAIMED"] = False
        return base
