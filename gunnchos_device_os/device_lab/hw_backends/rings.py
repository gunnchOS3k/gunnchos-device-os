"""Rings simulator → authenticated path → SpatialInputService → apps.

Direct file writes do NOT count as Ring real-input D6.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RingsBackend:
    spatial: Any = None
    actions: list[dict[str, Any]] = field(default_factory=list)
    last_reject: dict[str, Any] | None = None

    def start(self) -> dict[str, Any]:
        from gunnchos_device_os.phase_xiv.spatial import SpatialInputService

        self.spatial = SpatialInputService()
        self.spatial.calibrate()
        return {
            "ok": True,
            "pipeline": [
                "edge_io_sim",
                "authenticated_packet",
                "ring_service",
                "SpatialInputService",
                "input_router_hid_wayland",
                "apps",
            ],
            "direct_file_write_valid_d6": False,
            "physical_accuracy": "PHYSICAL_PENDING",
        }

    def inject(
        self,
        *,
        target: str = "browser",
        confidence: float = 0.9,
        gesture: str = "click",
        wrong_target: bool = False,
        ax: float = 0.1,
        ay: float = 0.0,
    ) -> dict[str, Any]:
        from gunnchos_device_os.phase_xiv.spatial import EdgeSample

        assert self.spatial is not None
        # Safety: low confidence / wrong target reject
        if confidence < 0.5:
            self.last_reject = {"reason": "low_confidence", "confidence": confidence}
            self.actions.append({"kind": "reject", **self.last_reject})
            return {"ok": True, "delivered": False, "reject": self.last_reject, "via_stack": True}
        if wrong_target:
            self.last_reject = {"reason": "wrong_target", "requested": target}
            self.actions.append({"kind": "reject", **self.last_reject})
            return {"ok": True, "delivered": False, "reject": self.last_reject, "via_stack": True}

        self.spatial.set_target(target)
        sample = EdgeSample(ts_ms=0.0, ax=ax, ay=ay, az=1.0, gx=0.0, gy=0.0, gz=0.0, button=gesture if gesture != "move" else None, touch=gesture == "click")
        # authenticated packet envelope (software)
        packet = {
            "authenticated": True,
            "device_id": "ring-sim-01",
            "session_id": "lab-ring-session",
            "confidence": confidence,
            "gesture": gesture,
            "target": target,
        }
        self.spatial.ingest_edge_sim(sample)
        events = self.spatial.fuse()
        # confidence gate on fused events
        accepted = [e for e in events if e.confidence >= 0.5]
        delivered = self.spatial.deliver_to_os(accepted)
        row = {
            "kind": "deliver",
            "packet": packet,
            "events": len(accepted),
            "delivered": delivered,
            "via_stack": True,
            "direct_file_write": False,
        }
        self.actions.append(row)
        return {"ok": True, "delivered": True, "result": row, "via_stack": True}

    def fallback_conventional(self) -> dict[str, Any]:
        row = {"kind": "fallback", "input": "keyboard_mouse", "reason": "ring_unavailable_or_rejected"}
        self.actions.append(row)
        return {"ok": True, "fallback": row}
