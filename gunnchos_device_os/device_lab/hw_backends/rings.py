"""Rings simulator → authenticated path → SpatialInputService → apps.

Direct file writes do NOT count as Ring real-input D6.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RingsBackend:
    spatial: Any = None
    router: Any = None
    surfaces: Any = None
    evidence_dir: Path | None = None
    repo_root: Path | None = None
    actions: list[dict[str, Any]] = field(default_factory=list)
    last_reject: dict[str, Any] | None = None

    def start(self, *, evidence_dir: Path | None = None, repo_root: Path | None = None) -> dict[str, Any]:
        from gunnchos_device_os.device_lab.apps.surfaces import (
            BrowserSurface,
            DocumentSurface,
            GameSurface,
            SurfaceRegistry,
        )
        from gunnchos_device_os.device_lab.input_router import InputRouter
        from gunnchos_device_os.phase_xiv.spatial import SpatialInputService

        self.evidence_dir = evidence_dir
        self.repo_root = repo_root
        doc_ev = (evidence_dir / "document") if evidence_dir else None
        br_ev = (evidence_dir / "browser") if evidence_dir else None
        game_ev = (evidence_dir / "game") if evidence_dir else None
        self.surfaces = SurfaceRegistry(
            document=DocumentSurface(evidence_dir=doc_ev),
            browser=BrowserSurface(evidence_dir=br_ev),
            games=GameSurface(evidence_dir=game_ev, repo_root=repo_root),
        )
        self.router = InputRouter(surfaces=self.surfaces)
        self.spatial = SpatialInputService(router=self.router)
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
            "surfaces": list(self.surfaces.snapshots().keys()),
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

        if self.spatial is None or self.router is None:
            self.start(evidence_dir=self.evidence_dir, repo_root=self.repo_root)

        assert self.spatial is not None
        assert self.router is not None

        # Safety: low confidence / wrong target reject
        if confidence < 0.5:
            self.last_reject = {"reason": "low_confidence", "confidence": confidence}
            self.actions.append({"kind": "reject", **self.last_reject})
            return {"ok": True, "delivered": False, "reject": self.last_reject, "via_stack": True}
        if wrong_target:
            self.last_reject = {"reason": "wrong_target", "requested": target}
            self.actions.append({"kind": "reject", **self.last_reject})
            return {"ok": True, "delivered": False, "reject": self.last_reject, "via_stack": True}

        before = self.surfaces.by_target(target).snapshot() if self.surfaces else None
        self.spatial.set_target(target)
        self.router.focus(target)

        sample = EdgeSample(
            ts_ms=0.0,
            ax=ax,
            ay=ay,
            az=1.0,
            gx=0.0,
            gy=0.0,
            gz=0.0,
            button=gesture if gesture != "move" else None,
            touch=gesture == "click",
        )
        # authenticated packet envelope (software Ring service)
        packet = {
            "authenticated": True,
            "device_id": "ring-sim-01",
            "session_id": "lab-ring-session",
            "confidence": confidence,
            "gesture": gesture,
            "target": target,
            "ring_service": "gunnchos.ring.service.v1",
        }
        self.spatial.ingest_edge_sim(sample)
        # For document typing proof, also ingest an explicit type sample when click
        if target == "libreoffice" and gesture == "click":
            self.spatial.ingest_edge_sim(
                EdgeSample(
                    ts_ms=1.0,
                    ax=0.0,
                    ay=0.0,
                    az=1.0,
                    gx=0.0,
                    gy=0.0,
                    gz=0.0,
                    button="click",
                    touch=True,
                )
            )
        if target == "browser" and gesture == "click":
            # scroll + click for richer GUI state
            self.spatial.ingest_edge_sim(
                EdgeSample(
                    ts_ms=2.0,
                    ax=0.0,
                    ay=0.0,
                    az=1.0,
                    gx=0.0,
                    gy=0.0,
                    gz=0.4,
                    button="scroll",
                    touch=False,
                )
            )
        events = self.spatial.fuse()
        # Apply packet confidence gate on fused events
        accepted = []
        for e in events:
            e.confidence = min(e.confidence, confidence)
            if e.confidence >= 0.5:
                accepted.append(e)
        delivery = self.spatial.deliver_to_os(accepted)
        after = self.surfaces.by_target(target).snapshot() if self.surfaces else None
        mutated = bool(delivery.get("app_state_changed")) and before != after
        # delivered is honest: only True when app state actually changed via stack
        delivered = mutated and bool(delivery.get("delivered", 0) > 0)
        row = {
            "kind": "deliver",
            "packet": packet,
            "events": len(accepted),
            "delivery": delivery,
            "delivered": delivered,
            "app_state_changed": mutated,
            "before": before,
            "after": after,
            "via_stack": True,
            "direct_file_write": False,
        }
        self.actions.append(row)
        return {
            "ok": delivered,
            "delivered": delivered,
            "result": row,
            "via_stack": True,
            "app_state_changed": mutated,
            "before": before,
            "after": after,
        }

    def fallback_conventional(self) -> dict[str, Any]:
        """Fallback to conventional keyboard/mouse — not RING_TO_REAL_APPLICATION_INPUT_PASS."""
        from gunnchos_device_os.device_lab.apps.surfaces import BrowserSurface
        from gunnchos_device_os.device_lab.virtualization.guest_input import inject_key

        surface = (self.surfaces.browser if self.surfaces else BrowserSurface())
        inj = inject_key(monitor_sock=None, key="a", hybrid_surface=surface)
        row = {
            "kind": "fallback",
            "input": "keyboard_mouse",
            "reason": "ring_unavailable_or_rejected",
            "injection": inj,
            "RING_TO_REAL_APPLICATION_INPUT_PASS": False,
            "RING_SPATIAL_ACCURACY": "SIMULATED",
        }
        self.actions.append(row)
        return {"ok": bool(inj.get("ok")), "fallback": row}
