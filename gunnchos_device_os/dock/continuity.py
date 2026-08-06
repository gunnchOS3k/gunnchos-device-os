"""Dock continuity engine: attach/detach, routes, session, restore, degraded/safe undock."""
from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.identity import (
    new_device_id,
    new_dock_event_id,
    new_session_id,
    sha256_json,
    utc_now_iso,
)

from .capabilities import load_capabilities


LAYOUT_PROFILES = {
    "handheld": {"displays": ["internal"], "primary": "internal"},
    "docked-extend": {"displays": ["internal", "external"], "primary": "external"},
    "docked-mirror": {"displays": ["internal", "external"], "primary": "internal", "mode": "mirror"},
    "degraded-internal-only": {"displays": ["internal"], "primary": "internal", "degraded": True},
}


@dataclass
class DockContinuityEngine:
    device_id: str = field(default_factory=lambda: new_device_id("hh"))
    dock_id: str | None = None
    session_id: str = field(default_factory=lambda: new_session_id())
    docked: bool = False
    layout_profile: str = "handheld"
    apps: list[str] = field(default_factory=lambda: ["launcher", "notes"])
    input_map: dict[str, str] = field(
        default_factory=lambda: {"primary": "touch", "secondary": "buttons"}
    )
    identity: dict[str, Any] = field(default_factory=lambda: {"user": "local", "auth": "device-bound"})
    save_blob: dict[str, Any] = field(default_factory=lambda: {"slot": 1, "progress": 0})
    audio_route: str = "internal"
    power_state: str = "battery"
    network_route: str = "wlan"
    display_state: dict[str, Any] = field(default_factory=dict)
    peripherals: list[str] = field(default_factory=list)
    degraded: bool = False
    last_snapshot: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    latencies_ms: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.display_state = {"internal": True, "external": False}
        self.capabilities = load_capabilities()

    def _event(self, kind: str, **extra: Any) -> dict[str, Any]:
        ev = {
            "event_id": new_dock_event_id(),
            "kind": kind,
            "timestamp": utc_now_iso(),
            **extra,
        }
        self.events.append(ev)
        return ev

    def snapshot_session(self) -> dict[str, Any]:
        snap = {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "dock_id": self.dock_id,
            "docked": self.docked,
            "layout_profile": self.layout_profile,
            "apps": list(self.apps),
            "input_map": dict(self.input_map),
            "identity": dict(self.identity),
            "save_blob": dict(self.save_blob),
            "save_checksum": sha256_json(self.save_blob),
            "audio_route": self.audio_route,
            "power_state": self.power_state,
            "network_route": self.network_route,
            "display_state": dict(self.display_state),
            "peripherals": list(self.peripherals),
            "degraded": self.degraded,
        }
        self.last_snapshot = copy.deepcopy(snap)
        self._event("session_snapshot", save_checksum=snap["save_checksum"])
        return snap

    def attach(
        self,
        dock_id: str,
        *,
        dock_class: str = "generic-display-dock",
        ports: list[str] | None = None,
        external_display: bool = True,
        ethernet: bool = True,
        audio_dock: bool = True,
        power_passthrough: bool = True,
        latency_ms: int = 12,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        before = self.observe(phase="before_attach")
        self.dock_id = dock_id
        self.docked = True
        self.degraded = False
        self.layout_profile = "docked-extend" if external_display else "docked-mirror"
        self.display_state = {"internal": True, "external": bool(external_display)}
        self.peripherals = list(ports or ["usb-c", "hdmi-or-dp"])
        if ethernet:
            self.network_route = "ethernet-via-dock"
        if audio_dock:
            self.audio_route = "dock-audio"
        if power_passthrough:
            self.power_state = "dock-power"
        self.input_map = {"primary": "keyboard", "secondary": "mouse", "fallback": "touch"}
        self.latencies_ms["attach"] = latency_ms or int((time.perf_counter() - t0) * 1000)
        snap = self.snapshot_session()
        after = self.observe(phase="after_attach")
        ev = self._event(
            "attach",
            dock_class=dock_class,
            before=before,
            after=after,
            snapshot=snap,
        )
        return ev

    def detach(self, *, safe: bool = True, latency_ms: int = 10) -> dict[str, Any]:
        before = self.observe(phase="before_detach")
        prior_snap = self.last_snapshot or self.snapshot_session()
        self.docked = False
        self.dock_id = None
        self.layout_profile = "handheld"
        self.display_state = {"internal": True, "external": False}
        self.peripherals = []
        self.network_route = "wlan"
        self.audio_route = "internal"
        self.power_state = "battery"
        self.input_map = {"primary": "touch", "secondary": "buttons"}
        self.degraded = False
        # Continuity: preserve apps, identity, save
        self.apps = list(prior_snap.get("apps") or self.apps)
        self.identity = dict(prior_snap.get("identity") or self.identity)
        self.save_blob = dict(prior_snap.get("save_blob") or self.save_blob)
        self.latencies_ms["detach"] = latency_ms
        if not safe:
            self.errors.append("unsafe_undock_observed")
        after = self.observe(phase="after_detach")
        return self._event("detach", safe=safe, before=before, after=after)

    def safe_undock(self) -> dict[str, Any]:
        self.snapshot_session()
        return self.detach(safe=True)

    def enter_degraded_mode(self, reason: str = "external_display_lost") -> dict[str, Any]:
        self.degraded = True
        self.layout_profile = "degraded-internal-only"
        self.display_state = {"internal": True, "external": False}
        self.audio_route = "internal"
        return self._event("degraded_mode", reason=reason)

    def recover_interruption(self) -> dict[str, Any]:
        if not self.last_snapshot:
            self.errors.append("no_snapshot_for_recovery")
            return self._event("interruption_recovery", ok=False)
        snap = self.last_snapshot
        self.session_id = snap["session_id"]
        self.apps = list(snap["apps"])
        self.identity = dict(snap["identity"])
        self.save_blob = dict(snap["save_blob"])
        self.input_map = dict(snap["input_map"])
        # Prefer internal-safe restore after interruption
        self.docked = False
        self.layout_profile = "handheld"
        self.display_state = {"internal": True, "external": False}
        self.degraded = False
        return self._event(
            "interruption_recovery",
            ok=True,
            save_checksum=sha256_json(self.save_blob),
        )

    def restore_from_snapshot(self, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        snap = snapshot or self.last_snapshot
        if not snap:
            raise ValueError("no snapshot available")
        self.session_id = snap["session_id"]
        self.device_id = snap["device_id"]
        self.apps = list(snap["apps"])
        self.identity = dict(snap["identity"])
        self.save_blob = dict(snap["save_blob"])
        self.input_map = dict(snap["input_map"])
        self.audio_route = snap.get("audio_route", self.audio_route)
        self.network_route = snap.get("network_route", self.network_route)
        self.power_state = snap.get("power_state", self.power_state)
        self.layout_profile = snap.get("layout_profile", self.layout_profile)
        self.display_state = dict(snap.get("display_state") or self.display_state)
        self.docked = bool(snap.get("docked"))
        self.dock_id = snap.get("dock_id")
        return self._event("restore", save_checksum=sha256_json(self.save_blob))

    def observe(self, *, phase: str) -> dict[str, Any]:
        return {
            "phase": phase,
            "device_id": self.device_id,
            "dock_id": self.dock_id,
            "docked": self.docked,
            "ports": list(self.peripherals),
            "display": dict(self.display_state),
            "inputs": dict(self.input_map),
            "network": self.network_route,
            "apps": list(self.apps),
            "session_id": self.session_id,
            "save_checksum": sha256_json(self.save_blob),
            "audio": self.audio_route,
            "power": self.power_state,
            "layout_profile": self.layout_profile,
            "degraded": self.degraded,
        }

    def continuity_report(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "session_id": self.session_id,
            "docked": self.docked,
            "layout_profiles_available": sorted(LAYOUT_PROFILES.keys()),
            "events": list(self.events),
            "latencies_ms": dict(self.latencies_ms),
            "errors": list(self.errors),
            "last_snapshot": self.last_snapshot,
            "detection_policy": self.capabilities.get("detection_policy"),
        }
