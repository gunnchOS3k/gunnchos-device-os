"""SpatialInputService — fusion pipeline from edge-io sim → OS input targets.

Targets: LibreOffice, browser, games.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


TARGETS = ("libreoffice", "browser", "games")


@dataclass
class EdgeSample:
    """Simulated edge-io measurement-node sample."""

    ts_ms: float
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    touch: bool = False
    button: str | None = None


@dataclass
class OsPointerEvent:
    kind: str  # move | click | scroll | key
    x: float
    y: float
    target: str
    confidence: float
    source: str = "spatial_fusion"


class SpatialInputService:
    def __init__(self):
        self.samples: list[EdgeSample] = []
        self.events: list[OsPointerEvent] = []
        self.fusion_state = {"x": 0.0, "y": 0.0, "calibrated": False}
        self.active_target = "browser"

    def ingest_edge_sim(self, sample: EdgeSample) -> None:
        self.samples.append(sample)

    def calibrate(self) -> dict[str, Any]:
        self.fusion_state["calibrated"] = True
        self.fusion_state["x"] = 0.0
        self.fusion_state["y"] = 0.0
        return dict(self.fusion_state)

    def set_target(self, target: str) -> None:
        if target not in TARGETS:
            raise ValueError(target)
        self.active_target = target

    def fuse(self) -> list[OsPointerEvent]:
        if not self.fusion_state["calibrated"]:
            raise RuntimeError("not_calibrated")
        out: list[OsPointerEvent] = []
        for s in self.samples:
            # simple complementary fusion: accel → position delta, gyro → fine tip
            dx = s.ax * 0.4 + s.gx * 0.05
            dy = s.ay * 0.4 + s.gy * 0.05
            self.fusion_state["x"] += dx
            self.fusion_state["y"] += dy
            conf = max(0.1, min(1.0, 1.0 - abs(s.az - 1.0) * 0.2))
            out.append(
                OsPointerEvent(
                    kind="move",
                    x=self.fusion_state["x"],
                    y=self.fusion_state["y"],
                    target=self.active_target,
                    confidence=conf,
                )
            )
            if s.touch or s.button == "click":
                out.append(
                    OsPointerEvent(
                        kind="click",
                        x=self.fusion_state["x"],
                        y=self.fusion_state["y"],
                        target=self.active_target,
                        confidence=conf,
                    )
                )
            if s.button == "scroll":
                out.append(
                    OsPointerEvent(
                        kind="scroll",
                        x=0.0,
                        y=s.gz,
                        target=self.active_target,
                        confidence=conf,
                    )
                )
        self.events.extend(out)
        self.samples.clear()
        return out

    def deliver_to_os(self, events: list[OsPointerEvent] | None = None) -> dict[str, Any]:
        events = events if events is not None else self.events[-20:]
        by_target: dict[str, int] = {t: 0 for t in TARGETS}
        for e in events:
            by_target[e.target] = by_target.get(e.target, 0) + 1
        return {
            "ok": True,
            "delivered": len(events),
            "by_target": by_target,
            "physical_accuracy": "PHYSICAL_PENDING",
        }

    def e2e_edge_to_apps(self) -> dict[str, Any]:
        self.calibrate()
        results = {}
        for target in TARGETS:
            self.set_target(target)
            now = time.time() * 1000
            self.ingest_edge_sim(EdgeSample(now, 0.2, -0.1, 1.0, 0.01, 0.0, 0.0))
            self.ingest_edge_sim(EdgeSample(now + 16, 0.1, 0.05, 0.98, 0.0, 0.02, 0.1, button="click"))
            if target == "browser":
                self.ingest_edge_sim(EdgeSample(now + 32, 0.0, 0.0, 1.0, 0.0, 0.0, 0.3, button="scroll"))
            fused = self.fuse()
            results[target] = {
                "events": len(fused),
                "kinds": sorted({e.kind for e in fused}),
                "min_confidence": min(e.confidence for e in fused),
            }
        delivery = self.deliver_to_os()
        ok = all(results[t]["events"] > 0 for t in TARGETS) and delivery["ok"]
        return {"ok": ok, "targets": results, "delivery": delivery, "supported_targets": list(TARGETS)}
