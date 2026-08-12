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
    # Optional live guest injection path (QEMU monitor / guest agent)
    guest_monitor_sock: Path | None = None
    guest_agent: Any = None
    guest_process: Any = None  # hybrid host process with observable state

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

        # Optional: also push through OS input path into live guest / hybrid process.
        guest_or_hybrid: dict[str, Any] = {"attempted": False}
        if delivered:
            guest_or_hybrid = self._inject_os_input_path(target=target, gesture=gesture)

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
            "os_input_path": guest_or_hybrid,
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
            "os_input_path": guest_or_hybrid,
        }

    def _inject_os_input_path(self, *, target: str, gesture: str) -> dict[str, Any]:
        """Wire Ring event through conventional OS input into guest or hybrid process.

        RING_TO_REAL_APPLICATION_INPUT_PASS is only earned when guest virtio-serial
        (non-stub) observes the input. Hybrid surface mutation alone is not enough.
        Spatial accuracy remains SIMULATED.
        """
        from gunnchos_device_os.device_lab.virtualization.guest_input import inject_key, inject_pointer

        out: dict[str, Any] = {
            "attempted": True,
            "RING_SPATIAL_ACCURACY": "SIMULATED",
            "RING_TO_REAL_APPLICATION_INPUT_PASS": False,
        }
        # Hybrid process path (observable host process / surface already mutated via stack)
        if self.guest_process is not None and hasattr(self.guest_process, "apply_hid"):
            before = self.guest_process.snapshot() if hasattr(self.guest_process, "snapshot") else None
            applied = self.guest_process.apply_hid({"kind": "click" if gesture == "click" else "key", "text": "r"})
            after = self.guest_process.snapshot() if hasattr(self.guest_process, "snapshot") else None
            out["hybrid_process"] = {
                "ok": bool(applied.get("mutated")) or before != after,
                "before": before,
                "after": after,
                "path": "hybrid_process",
            }

        if self.guest_monitor_sock is not None or self.guest_agent is not None:
            if gesture == "click":
                inj = inject_pointer(
                    monitor_sock=self.guest_monitor_sock,
                    agent=self.guest_agent,
                    x=40,
                    y=40,
                )
            else:
                inj = inject_key(
                    monitor_sock=self.guest_monitor_sock,
                    key="r",
                    agent=self.guest_agent,
                )
            out["guest_injection"] = inj
            transport = None
            stub = True
            if self.guest_agent is not None:
                try:
                    observe = self.guest_agent.call("input_observe", kind=gesture, target=target)
                    out["guest_observe"] = observe
                    transport = observe.get("transport")
                    stub = bool(observe.get("stub", True))
                except Exception as exc:  # noqa: BLE001
                    out["guest_observe_error"] = str(exc)
            # Earn PASS only with non-stub virtio-serial observation + accepted injection
            if (
                inj.get("ok")
                and transport in {"virtio_serial", "virtio-serial"}
                and not stub
                and (out.get("guest_observe") or {}).get("observed")
            ):
                out["path"] = "guest"
                out["RING_TO_REAL_APPLICATION_INPUT_PASS"] = True
                out["earned_via"] = "ring→SpatialInput→OS_input→guest_agent_virtio_serial"
            else:
                out["path"] = "guest_attempted"
                out["blocker"] = (
                    "Guest virtio-serial input_observe not proven (stub or missing); "
                    "spatial remains SIMULATED"
                )
        else:
            out["path"] = "hybrid_process" if out.get("hybrid_process") else "unbound"
            out["blocker"] = "No guest monitor/agent bound; hybrid Lab surfaces only"
        return out

    def fallback_conventional(self) -> dict[str, Any]:
        """Fallback to conventional keyboard/mouse — not RING_TO_REAL_APPLICATION_INPUT_PASS."""
        from gunnchos_device_os.device_lab.apps.surfaces import BrowserSurface
        from gunnchos_device_os.device_lab.virtualization.guest_input import inject_key, inject_pointer

        surface = (self.surfaces.browser if self.surfaces else BrowserSurface())
        # Prefer click on browser (keyboard alone used to no-op on BrowserSurface).
        inj = inject_pointer(monitor_sock=None, hybrid_surface=surface, x=12, y=12)
        if not inj.get("ok"):
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
