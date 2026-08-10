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
    def __init__(self, router: Any | None = None):
        self.samples: list[EdgeSample] = []
        self.events: list[OsPointerEvent] = []
        self.fusion_state = {"x": 0.0, "y": 0.0, "calibrated": False}
        self.active_target = "browser"
        # Optional InputRouter — when bound, deliver_to_os mutates real app surfaces
        self.router = router

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
        """Deliver fused events into the OS input path.

        When an InputRouter is bound, each accepted event is injected via virtual
        HID / Wayland into the focused app surface and must produce an observable
        app-state mutation. Event counts alone are NOT sufficient for D6.
        """
        events = events if events is not None else self.events[-20:]
        by_target: dict[str, int] = {t: 0 for t in TARGETS}
        for e in events:
            by_target[e.target] = by_target.get(e.target, 0) + 1

        mutations: list[dict[str, Any]] = []
        app_state_changed = False
        if self.router is not None:
            for e in events:
                # Prefer actionable kinds for mutation proof; still deliver moves
                result = self.router.deliver(e)
                mutations.append(result)
                if result.get("mutated"):
                    app_state_changed = True
            delivered_count = sum(1 for m in mutations if m.get("delivered"))
            return {
                "ok": app_state_changed,
                "delivered": delivered_count,
                "by_target": by_target,
                "mutations": mutations,
                "app_state_changed": app_state_changed,
                "via": "input_router_hid_wayland",
                "direct_file_write": False,
                "physical_accuracy": "PHYSICAL_PENDING",
            }

        # No router bound: honest partial — counts only, not D6 app mutation
        return {
            "ok": False,
            "delivered": 0,
            "by_target": by_target,
            "mutations": [],
            "app_state_changed": False,
            "via": "event_count_only",
            "note": "SpatialInputService without InputRouter cannot claim Ring D6 app mutation",
            "physical_accuracy": "PHYSICAL_PENDING",
        }

    def e2e_edge_to_apps(self) -> dict[str, Any]:
        # Bind a Lab InputRouter so delivery mutates real app surfaces (D6 path).
        if self.router is None:
            from gunnchos_device_os.device_lab.input_router import InputRouter

            self.router = InputRouter()
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
        ok = (
            all(results[t]["events"] > 0 for t in TARGETS)
            and delivery.get("app_state_changed")
            and bool(delivery.get("delivered", 0) > 0)
        )
        return {
            "ok": ok,
            "targets": results,
            "delivery": delivery,
            "supported_targets": list(TARGETS),
            "app_snapshots": self.router.surfaces.snapshots() if self.router else None,
        }
