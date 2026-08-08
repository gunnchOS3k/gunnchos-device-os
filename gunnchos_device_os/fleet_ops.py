"""Carrier-grade fleet ops *simulation* — enrollment, rings, canary, health.

Not production MDM. No remote fleet server. All state is in-process for
digital validation of ops workflows (enroll → ring → canary → rollback).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from gunnchos_device_os.identity import sha256_text, utc_now_iso
from gunnchos_device_os.security_event_log import log_event


CLAIM_BOUNDARY = (
    "Fleet ops simulation only. No remote MDM server, no carrier certification, "
    "no production enrollment authority, no live staged rollout to hardware."
)


class EnrollmentState(str, Enum):
    UNENROLLED = "unenrolled"
    PENDING = "pending"
    ENROLLED = "enrolled"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class UpdateRing(str, Enum):
    DEV = "dev"
    CANARY = "canary"
    EARLY = "early"
    BROAD = "broad"
    FROZEN = "frozen"


class DeviceHealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class FleetDevice:
    device_id: str
    cohort: str = "default"
    ring: UpdateRing = UpdateRing.DEV
    enrollment: EnrollmentState = EnrollmentState.UNENROLLED
    enrolled_at: str | None = None
    inventory: dict[str, Any] = field(default_factory=dict)
    health: DeviceHealthState = DeviceHealthState.UNKNOWN
    last_diagnostic: dict[str, Any] = field(default_factory=dict)
    security_version: int = 1
    current_version: str = "0.1.0-evt1-alpha"
    target_version: str | None = None
    canary: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["ring"] = self.ring.value
        d["enrollment"] = self.enrollment.value
        d["health"] = self.health.value
        return d


@dataclass
class SloStub:
    """SLO stub definitions — targets only, not measured production SLOs."""

    name: str
    target: float
    window: str
    unit: str
    measured: float | None = None  # None until a sim observation is recorded
    status: str = "stub_unmeasured"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_SLO_STUBS: list[SloStub] = [
    SloStub("enrollment_success_rate", 0.99, "7d", "ratio"),
    SloStub("update_apply_success_rate", 0.995, "7d", "ratio"),
    SloStub("rollback_completion_p95_s", 300.0, "30d", "seconds"),
    SloStub("fleet_health_reporting_freshness_s", 900.0, "1d", "seconds"),
    SloStub("security_telemetry_delivery_rate", 0.99, "7d", "ratio"),
]


@dataclass
class FleetOpsSimulator:
    """In-memory fleet ops control plane simulation."""

    org_id: str = "campus-sim"
    devices: dict[str, FleetDevice] = field(default_factory=dict)
    rollout_id: str | None = None
    canary_percent: float = 5.0
    canary_failures: int = 0
    canary_successes: int = 0
    canary_abort_threshold: int = 2
    slo_stubs: list[SloStub] = field(default_factory=lambda: list(DEFAULT_SLO_STUBS))
    inventory_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def claim_boundary(self) -> str:
        return CLAIM_BOUNDARY

    def _emit(self, kind: str, details: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "kind": kind,
            "at": utc_now_iso(),
            "details": details,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.events.append(entry)
        log_event(f"fleet_{kind}", details)
        return entry

    # --- enrollment ---
    def enroll(
        self,
        device_id: str,
        *,
        cohort: str = "default",
        ring: UpdateRing | str = UpdateRing.DEV,
        inventory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ring_e = ring if isinstance(ring, UpdateRing) else UpdateRing(ring)
        inv = dict(inventory or {})
        inv.setdefault("device_id", device_id)
        inv.setdefault("org_id", self.org_id)
        inv.setdefault("sku_class", inv.get("sku_class", "profile_declared"))
        dev = FleetDevice(
            device_id=device_id,
            cohort=cohort,
            ring=ring_e,
            enrollment=EnrollmentState.ENROLLED,
            enrolled_at=utc_now_iso(),
            inventory=inv,
            health=DeviceHealthState.HEALTHY,
            canary=ring_e == UpdateRing.CANARY,
        )
        self.devices[device_id] = dev
        self.inventory_index[device_id] = dict(inv)
        self._emit("enroll", {"device_id": device_id, "ring": ring_e.value, "cohort": cohort})
        return {
            "device_id": device_id,
            "enrollment": EnrollmentState.ENROLLED.value,
            "ring": ring_e.value,
            "enrolled_at": dev.enrolled_at,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def revoke(self, device_id: str) -> dict[str, Any]:
        dev = self._require(device_id)
        dev.enrollment = EnrollmentState.REVOKED
        self._emit("revoke", {"device_id": device_id})
        return {"device_id": device_id, "enrollment": dev.enrollment.value, "mock": False}

    # --- rings / canary / rollback ---
    def assign_ring(self, device_id: str, ring: UpdateRing | str) -> dict[str, Any]:
        dev = self._require(device_id)
        ring_e = ring if isinstance(ring, UpdateRing) else UpdateRing(ring)
        dev.ring = ring_e
        dev.canary = ring_e == UpdateRing.CANARY
        self._emit("assign_ring", {"device_id": device_id, "ring": ring_e.value})
        return {"device_id": device_id, "ring": ring_e.value, "canary": dev.canary, "mock": False}

    def start_rollout(self, target_version: str, *, canary_percent: float | None = None) -> dict[str, Any]:
        self.rollout_id = f"rollout-{uuid4().hex[:10]}"
        if canary_percent is not None:
            self.canary_percent = canary_percent
        self.canary_failures = 0
        self.canary_successes = 0
        enrolled = [d for d in self.devices.values() if d.enrollment == EnrollmentState.ENROLLED]
        # Prefer explicit canary ring; else pick first N% of enrolled as canary.
        canaries = [d for d in enrolled if d.ring == UpdateRing.CANARY]
        if not canaries and enrolled:
            n = max(1, int(round(len(enrolled) * (self.canary_percent / 100.0))))
            canaries = enrolled[:n]
            for d in canaries:
                d.ring = UpdateRing.CANARY
                d.canary = True
        for d in canaries:
            d.target_version = target_version
        self._emit(
            "start_rollout",
            {
                "rollout_id": self.rollout_id,
                "target_version": target_version,
                "canary_count": len(canaries),
                "canary_percent": self.canary_percent,
            },
        )
        return {
            "rollout_id": self.rollout_id,
            "target_version": target_version,
            "canary_device_ids": [d.device_id for d in canaries],
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def report_canary_result(self, device_id: str, *, success: bool) -> dict[str, Any]:
        dev = self._require(device_id)
        if not dev.canary and dev.ring != UpdateRing.CANARY:
            raise ValueError(f"{device_id} is not in canary ring")
        if success:
            self.canary_successes += 1
            if dev.target_version:
                dev.current_version = dev.target_version
            dev.health = DeviceHealthState.HEALTHY
        else:
            self.canary_failures += 1
            dev.health = DeviceHealthState.CRITICAL
        aborted = self.canary_failures >= self.canary_abort_threshold
        self._emit(
            "canary_result",
            {
                "device_id": device_id,
                "success": success,
                "failures": self.canary_failures,
                "successes": self.canary_successes,
                "aborted": aborted,
            },
        )
        result: dict[str, Any] = {
            "device_id": device_id,
            "success": success,
            "canary_failures": self.canary_failures,
            "canary_successes": self.canary_successes,
            "aborted": aborted,
            "mock": False,
        }
        if aborted:
            result["rollback"] = self.rollback_rollout(reason="canary_abort_threshold")
        return result

    def promote_rings(self) -> dict[str, Any]:
        """Promote canary → early → broad when canary not aborted."""
        if self.canary_failures >= self.canary_abort_threshold:
            return {"promoted": False, "reason": "canary_aborted", "mock": False}
        if self.canary_successes < 1:
            return {"promoted": False, "reason": "no_canary_success", "mock": False}
        order = [UpdateRing.CANARY, UpdateRing.EARLY, UpdateRing.BROAD]
        moved = 0
        for d in self.devices.values():
            if d.enrollment != EnrollmentState.ENROLLED:
                continue
            if d.ring in order[:-1]:
                idx = order.index(d.ring)
                d.ring = order[idx + 1]
                d.canary = d.ring == UpdateRing.CANARY
                if d.target_version:
                    d.current_version = d.target_version
                moved += 1
        self._emit("promote_rings", {"moved": moved})
        return {"promoted": True, "moved": moved, "mock": False}

    def rollback_rollout(self, *, reason: str, known_good: str = "0.0.9-evt0") -> dict[str, Any]:
        rolled = []
        for d in self.devices.values():
            if d.target_version or d.canary:
                d.current_version = known_good
                d.target_version = None
                d.health = DeviceHealthState.DEGRADED
                rolled.append(d.device_id)
        self._emit("rollback", {"reason": reason, "known_good": known_good, "devices": rolled})
        return {
            "rolled_back": rolled,
            "known_good": known_good,
            "reason": reason,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    # --- health / diagnostics / inventory / security telemetry ---
    def update_health(
        self,
        device_id: str,
        state: DeviceHealthState | str,
        *,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dev = self._require(device_id)
        st = state if isinstance(state, DeviceHealthState) else DeviceHealthState(state)
        dev.health = st
        details = {"device_id": device_id, "health": st.value, "metrics": metrics or {}}
        self._emit("health", details)
        return {**details, "mock": False}

    def run_diagnostics(self, device_id: str) -> dict[str, Any]:
        dev = self._require(device_id)
        report = {
            "device_id": device_id,
            "enrollment": dev.enrollment.value,
            "ring": dev.ring.value,
            "version": dev.current_version,
            "health": dev.health.value,
            "inventory_hash": sha256_text(str(sorted(dev.inventory.items()))),
            "checks": {
                "enrollment_active": dev.enrollment == EnrollmentState.ENROLLED,
                "ring_assigned": True,
                "inventory_present": bool(dev.inventory),
            },
            "at": utc_now_iso(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        dev.last_diagnostic = report
        self._emit("diagnostics", {"device_id": device_id})
        return report

    def record_security_telemetry(self, device_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(device_id)
        # Redaction happens inside security_event_log.log_event
        entry = log_event(
            f"fleet_sec_{event_type}",
            {"device_id": device_id, **payload},
        )
        self._emit("security_telemetry", {"device_id": device_id, "event_type": event_type})
        return {
            "device_id": device_id,
            "event_type": event_type,
            "logged": True,
            "entry_mock": entry.get("mock", False),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def inventory_snapshot(self) -> dict[str, Any]:
        return {
            "org_id": self.org_id,
            "count": len(self.inventory_index),
            "devices": dict(self.inventory_index),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def observe_slo(self, name: str, measured: float) -> dict[str, Any]:
        for s in self.slo_stubs:
            if s.name == name:
                s.measured = measured
                if s.unit == "ratio":
                    s.status = "met_sim" if measured >= s.target else "missed_sim"
                else:
                    # lower-is-better latency/freshness style
                    s.status = "met_sim" if measured <= s.target else "missed_sim"
                return s.to_dict()
        raise ValueError(f"unknown SLO stub: {name}")

    def slo_report(self) -> dict[str, Any]:
        return {
            "slos": [s.to_dict() for s in self.slo_stubs],
            "note": "Stub targets with optional sim observations — not production SLOs",
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "org_id": self.org_id,
            "rollout_id": self.rollout_id,
            "canary_percent": self.canary_percent,
            "canary_failures": self.canary_failures,
            "canary_successes": self.canary_successes,
            "devices": {k: v.to_dict() for k, v in self.devices.items()},
            "inventory": self.inventory_snapshot(),
            "slos": self.slo_report(),
            "events": list(self.events[-50:]),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def _require(self, device_id: str) -> FleetDevice:
        if device_id not in self.devices:
            raise KeyError(f"device not enrolled: {device_id}")
        return self.devices[device_id]
