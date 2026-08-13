"""Multi-bearer policy: preference, failover, offline, reconnect, airplane.

WAN order: ethernet > wifi > cellular > ntn_simulated > offline.
Bluetooth is a local/PAN bearer — never a WAN failover path.
NTN simulated is research-only and never implied by RM520N-GL.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.connectivity.honest_tokens import honest_tokens
from gunnchos_device_os.connectivity_orchestrator import (
    BearerKind,
    BearerMetrics,
    ConnectivityOrchestrator,
    OrchestratorState,
)

WAN_PREFERENCE = (
    BearerKind.ETHERNET,
    BearerKind.WIFI,
    BearerKind.CELLULAR,
    BearerKind.NTN_SIMULATED,
    BearerKind.OFFLINE,
)

LOCAL_BEARERS = (BearerKind.BLUETOOTH,)

CLAIM_BOUNDARY = (
    "Software multi-bearer policy only. Bluetooth is PAN/local, not WAN. "
    "NTN path is simulated research class. No carrier attach, no TB5, no 6G."
)


@dataclass
class MultiBearerPolicy:
    wan_order: tuple[BearerKind, ...] = WAN_PREFERENCE
    allow_ntn_simulated: bool = True
    bluetooth_as_wan: bool = False  # never true in default policy
    orch: ConnectivityOrchestrator = field(default_factory=ConnectivityOrchestrator)
    airplane: bool = False
    last_wan: str = BearerKind.OFFLINE.value
    reconnect_count: int = 0

    def __post_init__(self) -> None:
        if self.bluetooth_as_wan:
            raise ValueError("bluetooth_as_wan is forbidden — Bluetooth is PAN/local only")

    def set_airplane(self, enabled: bool) -> dict[str, Any]:
        self.airplane = bool(enabled)
        if self.airplane:
            for kind in (
                BearerKind.ETHERNET,
                BearerKind.WIFI,
                BearerKind.CELLULAR,
                BearerKind.NTN_SIMULATED,
                BearerKind.BLUETOOTH,
            ):
                m = self.orch.metrics[kind.value]
                m.available = False
                m.loss_pct = 100.0
            result = self.orch.evaluate()
            return {
                "ok": True,
                "airplane": True,
                "active": result["active"],
                "state": result["state"],
                "claim_boundary": CLAIM_BOUNDARY,
                **honest_tokens(),
            }
        return {"ok": True, "airplane": False, "claim_boundary": CLAIM_BOUNDARY, **honest_tokens()}

    def enable_bluetooth_during_airplane(self) -> dict[str, Any]:
        """User may re-enable Bluetooth while airplane is on (PAN only)."""
        if not self.airplane:
            return {"ok": False, "reason": "airplane_not_active"}
        bt = self.orch.metrics[BearerKind.BLUETOOTH.value]
        bt.available = True
        bt.loss_pct = 0.0
        bt.latency_ms = min(bt.latency_ms, 40.0)
        # Do not promote BT to WAN; WAN stays offline.
        return {
            "ok": True,
            "airplane": True,
            "bluetooth_pan": True,
            "wan_active": BearerKind.OFFLINE.value,
            "claim_boundary": CLAIM_BOUNDARY,
            **honest_tokens(),
        }

    def apply_metrics(self, kind: BearerKind | str, metrics: BearerMetrics) -> None:
        key = kind.value if isinstance(kind, BearerKind) else kind
        if self.airplane and key not in (BearerKind.BLUETOOTH.value, BearerKind.OFFLINE.value):
            metrics.available = False
            metrics.loss_pct = 100.0
        if key == BearerKind.NTN_SIMULATED.value and not self.allow_ntn_simulated:
            metrics.available = False
        self.orch.update_metrics(key, metrics)

    def evaluate(self) -> dict[str, Any]:
        result = self.orch.evaluate()
        if result["active"] != BearerKind.OFFLINE.value:
            self.last_wan = result["active"]
        result["airplane"] = self.airplane
        result["wan_order"] = [k.value for k in self.wan_order]
        result["bluetooth_as_wan"] = False
        result["policy_claim_boundary"] = CLAIM_BOUNDARY
        result.update(honest_tokens())
        return result

    def failover(self, *, drop: str | None = None) -> dict[str, Any]:
        if drop:
            m = self.orch.metrics[drop]
            m.available = False
            m.loss_pct = 100.0
        before = self.orch.active_bearer.value
        result = self.evaluate()
        return {
            "ok": True,
            "from": before,
            "to": result["active"],
            "offline": result["active"] == BearerKind.OFFLINE.value,
            "evaluate": result,
            "claim_boundary": CLAIM_BOUNDARY,
            **honest_tokens(),
        }

    def reconnect(self) -> dict[str, Any]:
        """After drop: try last WAN if it became available, else policy order."""
        self.reconnect_count += 1
        if self.airplane:
            return {
                "ok": False,
                "reason": "airplane",
                "reconnect_count": self.reconnect_count,
                "active": BearerKind.OFFLINE.value,
                **honest_tokens(),
            }
        last = self.last_wan
        if last != BearerKind.OFFLINE.value and self.orch.metrics[last].available:
            self.orch.transition_to(BearerKind(last), reason="reconnect_last")
        result = self.evaluate()
        return {
            "ok": result["active"] != BearerKind.OFFLINE.value
            or result["state"] == OrchestratorState.OFFLINE.value,
            "reconnect_count": self.reconnect_count,
            "last_wan": last,
            "active": result["active"],
            "state": result["state"],
            "evaluate": result,
            "claim_boundary": CLAIM_BOUNDARY,
            **honest_tokens(),
        }

    def snapshot(self) -> dict[str, Any]:
        snap = self.orch.snapshot()
        snap.update(
            {
                "airplane": self.airplane,
                "last_wan": self.last_wan,
                "reconnect_count": self.reconnect_count,
                "wan_order": [k.value for k in self.wan_order],
                "bluetooth_as_wan": False,
                "policy_claim_boundary": CLAIM_BOUNDARY,
                **honest_tokens(),
            }
        )
        return snap
