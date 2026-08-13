"""Vendor-agnostic bearer capability interfaces for connectivity orchestration.

Three NTN-related classes, never collapsed:
  * TerrestrialBearer — RM520N-GL 5G NR Sub-6 + LTE; ntn_claimed=false
  * FutureNTNBearer / FutureNtnCapableModem — disabled SKU slot, not RM520N-GL
  * SimulatedNTNBearer — software NTN research path only

Bluetooth is PAN/local. Do not treat it as WAN failover.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any

from gunnchos_device_os.connectivity.honest_tokens import (
    CARRIER_ACCEPTED,
    DOCK_TB5,
    RM520N_GL_NTN,
    STANDARDIZED_6G,
    honest_tokens,
)


CLAIM_BOUNDARY = (
    "Software bearer capability interfaces only. No carrier attach, no live "
    "NTN certification, no fake current NTN. RM520N-GL is terrestrial 5G NR "
    "Sub-6 + LTE only. Future NTN-capable modem is a disabled SKU slot — not "
    "this modem. Dock is TB4 not TB5. STANDARDIZED_6G=false. CARRIER_ACCEPTED=false."
)


class NtnPathClass(str, Enum):
    """Honest NTN path taxonomy — do not infer from RM520N-GL."""

    TERRESTRIAL = "terrestrial"  # RM520N-GL; not NTN
    FUTURE_NTN_CAPABLE_MODEM = "future_ntn_capable_modem"  # SKU not selected
    SOFTWARE_NTN_SIMULATION = "software_ntn_simulation"


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
    notes: str = "Dock Ethernet over USB4/TB4 (not TB5) when profile allows"

    def connect(self) -> dict[str, Any]:
        if not self.supported:
            return {"ok": False, "reason": "unsupported"}
        self.metrics.available = True
        self.metrics.offline = False
        self.metrics.latency_ms = min(self.metrics.latency_ms, 5.0)
        self.metrics.loss_pct = 0.0
        self.metrics.security_score = max(self.metrics.security_score, 0.9)
        return {
            "ok": True,
            "bearer": self.name,
            "state": "connected",
            "dock_tb4": True,
            "dock_tb5": False,
        }

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
class BluetoothBearer(BearerCapability):
    """Bluetooth PAN/local path — never a WAN failover candidate."""

    name: str = "bluetooth"
    kind: str = "bluetooth"
    notes: str = "PAN/local only; not WAN failover"

    def connect(self) -> dict[str, Any]:
        if not self.supported:
            return {"ok": False, "reason": "unsupported"}
        self.metrics.available = True
        self.metrics.offline = False
        if self.metrics.signal_dbm is None:
            self.metrics.signal_dbm = -60.0
        self.metrics.latency_ms = min(self.metrics.latency_ms, 40.0)
        self.metrics.loss_pct = min(self.metrics.loss_pct, 2.0)
        return {
            "ok": True,
            "bearer": self.name,
            "state": "connected",
            "wan": False,
            "pan": True,
        }

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {"ok": True, "bearer": self.name, "state": "disconnected", "wan": False}


@dataclass
class TerrestrialBearer(BearerCapability):
    """Terrestrial cellular — RM520N-GL 5G NR Sub-6 + LTE. Not NTN, not 6G."""

    name: str = "terrestrial"
    kind: str = "cellular"
    notes: str = "RM520N-GL terrestrial 5G NR Sub-6 + LTE; ntn_claimed=false"
    modem_sku: str = "RM520N-GL"
    ntn_path_class: str = NtnPathClass.TERRESTRIAL.value

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
            "ntn_path_class": self.ntn_path_class,
            "ntn_claimed": False,
            "RM520N_GL_NTN": RM520N_GL_NTN,
            "STANDARDIZED_6G": STANDARDIZED_6G,
            "CARRIER_ACCEPTED": CARRIER_ACCEPTED,
            "DOCK_TB5": DOCK_TB5,
        }

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {
            "ok": True,
            "bearer": self.name,
            "state": "disconnected",
            "ntn_claimed": False,
            "RM520N_GL_NTN": False,
        }


@dataclass
class FutureNTNBearer(BearerCapability):
    """Future NTN-capable modem SKU slot — not RM520N-GL, not selected, disabled."""

    name: str = "future_ntn"
    kind: str = "ntn_future"
    supported: bool = False
    notes: str = "Future NTN-capable modem SKU not selected — not RM520N-GL"
    modem_sku: str | None = None
    ntn_path_class: str = NtnPathClass.FUTURE_NTN_CAPABLE_MODEM.value

    def connect(self) -> dict[str, Any]:
        return {
            "ok": False,
            "bearer": self.name,
            "reason": "future_ntn_capable_modem_not_selected",
            "fake_current_ntn": False,
            "ntn_path_class": self.ntn_path_class,
            "modem_sku": self.modem_sku,
            "not_rm520n_gl": True,
            "RM520N_GL_NTN": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def disconnect(self) -> dict[str, Any]:
        return {
            "ok": True,
            "bearer": self.name,
            "state": "idle",
            "fake_current_ntn": False,
            "not_rm520n_gl": True,
        }


# Explicit alias used by the NTN taxonomy docs/tests.
FutureNtnCapableModem = FutureNTNBearer


@dataclass
class SimulatedNTNBearer(BearerCapability):
    """Software NTN simulation — research path only. Not a modem SKU claim."""

    name: str = "ntn_simulated"
    kind: str = "ntn_simulated"
    notes: str = "Software NTN simulation only — not RM520N-GL NTN"
    ntn_path_class: str = NtnPathClass.SOFTWARE_NTN_SIMULATION.value

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
            "ntn_path_class": self.ntn_path_class,
            "RM520N_GL_NTN": False,
            "LIVE_NTN": False,
        }

    def disconnect(self) -> dict[str, Any]:
        self.metrics.available = False
        return {
            "ok": True,
            "bearer": self.name,
            "state": "disconnected",
            "simulated": True,
            "ntn_path_class": self.ntn_path_class,
        }


def build_default_bearers(*, ntn_simulated: bool = True) -> dict[str, BearerCapability]:
    return {
        "ethernet": EthernetBearer(),
        "wifi": WiFiBearer(),
        "bluetooth": BluetoothBearer(),
        "terrestrial": TerrestrialBearer(),
        "future_ntn": FutureNTNBearer(),
        "ntn_simulated": SimulatedNTNBearer(supported=ntn_simulated),
    }


def ntn_taxonomy(bearers: dict[str, BearerCapability] | None = None) -> dict[str, Any]:
    pool = bearers or build_default_bearers()
    return {
        "terrestrial": {
            "class": NtnPathClass.TERRESTRIAL.value,
            "sku": "RM520N-GL",
            "ntn": False,
            "tech": ["nr5g-sub6", "lte"],
        },
        "future_ntn_capable_modem": {
            "class": NtnPathClass.FUTURE_NTN_CAPABLE_MODEM.value,
            "sku": None,
            "selected": False,
            "not_rm520n_gl": True,
            "supported": pool["future_ntn"].supported,
        },
        "software_ntn_simulation": {
            "class": NtnPathClass.SOFTWARE_NTN_SIMULATION.value,
            "simulated": True,
            "live_ntn": False,
        },
        **honest_tokens(),
    }


def select_bearer(bearers: dict[str, BearerCapability]) -> dict[str, Any]:
    """WAN preference: ethernet > wifi > terrestrial > ntn_simulated > offline.

    FutureNTNBearer is never selected. Bluetooth is PAN/local, not WAN.
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
            **honest_tokens(),
        }
    return {
        "active": chosen.name,
        "kind": chosen.kind,
        "degraded": chosen.metrics.degraded,
        "offline": False,
        "metrics": chosen.metrics.to_dict(),
        "claim_boundary": CLAIM_BOUNDARY,
        "mock": False,
        **honest_tokens(),
    }
