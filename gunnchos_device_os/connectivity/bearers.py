"""Vendor-agnostic bearer capability interfaces for connectivity orchestration.

Connectivity manager depends only on these capability surfaces — not modem
SKUs. FutureNTNBearer is a modular placeholder (no fake current NTN claim).
SimulatedNTNBearer is the only NTN path usable in digital tests today.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Any


CLAIM_BOUNDARY = (
    "Software bearer capability interfaces only. No carrier attach, no live "
    "NTN certification, no fake current NTN. FutureNTNBearer is modular and "
    "disabled until a real NTN path exists."
)


@dataclass
class BearerMetricsView:
    available: bool = False
    signal_dbm: float | None = None
    latency_ms: float = 9999.0
    jitter_ms: float = 9999.0
    loss_pct: float = 100.0
    cost_per_mb: float = 1.0
    energy_mw: float = 1000.0
    security_score: float = 0.5
    user_preference: float = 0.5
    degraded: bool = False
    offline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_orchestrator_kwargs(self) -> dict[str, Any]:
        return {
            "available": self.available and not self.offline,
            "signal_dbm": self.signal_dbm,
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "loss_pct": self.loss_pct,
            "cost_per_mb": self.cost_per_mb,
            "energy_mw": self.energy_mw,
            "security_score": self.security_score,
            "user_preference": self.user_preference,
        }


@dataclass
class BearerCapability(ABC):
    """Capability interface shared by all bearers."""

    name: str
    kind: str
    supported: bool = True
    notes: str = ""
    metrics: BearerMetricsView = field(default_factory=BearerMetricsView)

    @abstractmethod
    def connect(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> dict[str, Any]:
        raise NotImplementedError

    def probe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "supported": self.supported,
            "available": self.metrics.available,
            "degraded": self.metrics.degraded,
            "offline": self.metrics.offline,
            "notes": self.notes,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }

    def update_metrics(self, **kwargs: Any) -> BearerMetricsView:
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
        return self.metrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "supported": self.supported,
            "notes": self.notes,
            "metrics": self.metrics.to_dict(),
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }


@dataclass
class EthernetBearer(BearerCapability):
    name: str = "ethernet"
    kind: str = "ethernet"
    notes: str = "Dock/Ethernet path when profile allows"

    def connect(self) -> dict[str, Any]:
        if not self.supported:
            return {"ok": False, "reason": "unsupported"}
        self.metrics.available = True
        self.metrics.offline = False
        self.metrics.latency_ms = min(self.metrics.latency_ms, 5.0)
        self.metrics.loss_pct = 0.0
        self.metrics.security_score = max(self.metrics.security_score, 0.9)
        return {"ok": True, "bearer": self.name, "state": "connected"}

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {"ok": True, "bearer": self.name, "state": "disconnected"}


@dataclass
class WiFiBearer(BearerCapability):
    name: str = "wifi"
    kind: str = "wifi"
    notes: str = "Local Wi-Fi path"

    def connect(self) -> dict[str, Any]:
        if not self.supported:
            return {"ok": False, "reason": "unsupported"}
        self.metrics.available = True
        self.metrics.offline = False
        if self.metrics.signal_dbm is None:
            self.metrics.signal_dbm = -55.0
        self.metrics.latency_ms = min(self.metrics.latency_ms, 25.0)
        self.metrics.loss_pct = min(self.metrics.loss_pct, 1.0)
        return {"ok": True, "bearer": self.name, "state": "connected"}

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {"ok": True, "bearer": self.name, "state": "disconnected"}


@dataclass
class TerrestrialBearer(BearerCapability):
    """Terrestrial cellular (e.g. RM520N-GL 5G sub-6 software path)."""

    name: str = "terrestrial"
    kind: str = "cellular"
    notes: str = "Terrestrial 5G sub-6 software path; no NTN claim"
    modem_sku: str = "RM520N-GL"

    def connect(self) -> dict[str, Any]:
        if not self.supported:
            return {"ok": False, "reason": "unsupported"}
        self.metrics.available = True
        self.metrics.offline = False
        if self.metrics.signal_dbm is None:
            self.metrics.signal_dbm = -90.0
        self.metrics.latency_ms = min(self.metrics.latency_ms, 45.0)
        self.metrics.loss_pct = min(self.metrics.loss_pct, 2.0)
        return {
            "ok": True,
            "bearer": self.name,
            "state": "connected",
            "modem_sku": self.modem_sku,
            "ntn_claimed": False,
        }

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {"ok": True, "bearer": self.name, "state": "disconnected", "ntn_claimed": False}


@dataclass
class FutureNTNBearer(BearerCapability):
    """Modular future NTN slot — intentionally unsupported / not claimed."""

    name: str = "future_ntn"
    kind: str = "ntn_future"
    supported: bool = False
    notes: str = "Future NTN placeholder — no fake current NTN"

    def connect(self) -> dict[str, Any]:
        return {
            "ok": False,
            "bearer": self.name,
            "reason": "future_ntn_not_available",
            "fake_current_ntn": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def disconnect(self) -> dict[str, Any]:
        return {"ok": True, "bearer": self.name, "state": "idle", "fake_current_ntn": False}


@dataclass
class SimulatedNTNBearer(BearerCapability):
    """Research/sim NTN path only — explicitly simulated."""

    name: str = "ntn_simulated"
    kind: str = "ntn_simulated"
    notes: str = "Simulated NTN research path only"

    def connect(self) -> dict[str, Any]:
        if not self.supported:
            return {"ok": False, "reason": "unsupported"}
        self.metrics.available = True
        self.metrics.offline = False
        self.metrics.degraded = True
        if self.metrics.signal_dbm is None:
            self.metrics.signal_dbm = -110.0
        self.metrics.latency_ms = max(self.metrics.latency_ms, 250.0)
        self.metrics.loss_pct = max(self.metrics.loss_pct, 5.0)
        return {
            "ok": True,
            "bearer": self.name,
            "state": "connected_simulated",
            "simulated": True,
            "fake_current_ntn": False,
        }

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {"ok": True, "bearer": self.name, "state": "disconnected", "simulated": True}


def build_default_bearers(*, ntn_simulated: bool = True) -> dict[str, BearerCapability]:
    return {
        "ethernet": EthernetBearer(),
        "wifi": WiFiBearer(),
        "terrestrial": TerrestrialBearer(),
        "future_ntn": FutureNTNBearer(),
        "ntn_simulated": SimulatedNTNBearer(supported=ntn_simulated),
    }


def select_bearer(bearers: dict[str, BearerCapability]) -> dict[str, Any]:
    """Simple preference: ethernet > wifi > terrestrial > ntn_simulated > offline.

    FutureNTNBearer is never selected.
    """
    preference = ("ethernet", "wifi", "terrestrial", "ntn_simulated")
    chosen = None
    for name in preference:
        b = bearers.get(name)
        if b is None or not b.supported:
            continue
        if b.metrics.available and not b.metrics.offline:
            chosen = b
            break
    if chosen is None:
        return {
            "active": "offline",
            "degraded": True,
            "offline": True,
            "reason": "no_available_bearer",
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }
    return {
        "active": chosen.name,
        "kind": chosen.kind,
        "degraded": chosen.metrics.degraded,
        "offline": False,
        "metrics": chosen.metrics.to_dict(),
        "claim_boundary": CLAIM_BOUNDARY,
        "mock": False,
    }
