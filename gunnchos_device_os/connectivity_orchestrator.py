"""Connectivity orchestrator — multi-bearer selection state machine.

Software decision layer only. Does NOT claim carrier certification, SIM
provisioning, radio firmware control, or live WWAN attach. Callers inject
observed metrics; the orchestrator scores and transitions bearers.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable


class OrchestratorState(str, Enum):
    IDLE = "idle"
    EVALUATING = "evaluating"
    CONNECTED = "connected"
    TRANSITIONING = "transitioning"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class BearerKind(str, Enum):
    ETHERNET = "ethernet"
    WIFI = "wifi"
    CELLULAR = "cellular"  # generic cellular path; no named carrier claim
    OFFLINE = "offline"


CLAIM_BOUNDARY = (
    "Software orchestrator only. No carrier attach, no SIM/eSIM control, "
    "no radio certification claim. Cellular is a generic bearer class."
)


@dataclass
class BearerMetrics:
    """Observed or injected path quality for one bearer."""

    available: bool = False
    signal_dbm: float | None = None  # higher (closer to 0) is better for RSSI-style
    latency_ms: float = 9999.0
    jitter_ms: float = 9999.0
    loss_pct: float = 100.0
    cost_per_mb: float = 1.0  # relative cost; lower better
    energy_mw: float = 1000.0  # estimated radio/path energy; lower better
    security_score: float = 0.0  # 0..1; higher better (e.g. trusted ethernet > open wifi)
    user_preference: float = 0.5  # 0..1 preference weight from policy/UI

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScoreWeights:
    availability: float = 10.0
    signal: float = 1.0
    latency: float = 2.0
    jitter: float = 1.5
    loss: float = 3.0
    cost: float = 1.0
    energy: float = 0.8
    security: float = 2.0
    user_preference: float = 1.5


@dataclass
class TransitionRecord:
    from_bearer: str
    to_bearer: str
    reason: str
    from_score: float
    to_score: float
    state_before: str
    state_after: str


@dataclass
class ConnectivityOrchestrator:
    """Evaluate bearers and transition active path with hysteresis."""

    weights: ScoreWeights = field(default_factory=ScoreWeights)
    hysteresis: float = 5.0  # required score delta to switch away from active
    active_bearer: BearerKind = BearerKind.OFFLINE
    state: OrchestratorState = OrchestratorState.IDLE
    metrics: dict[str, BearerMetrics] = field(default_factory=dict)
    history: list[TransitionRecord] = field(default_factory=list)
    faults: set[str] = field(default_factory=set)
    _listeners: list[Callable[[TransitionRecord], None]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.metrics:
            self.metrics = {
                BearerKind.ETHERNET.value: BearerMetrics(),
                BearerKind.WIFI.value: BearerMetrics(),
                BearerKind.CELLULAR.value: BearerMetrics(),
                BearerKind.OFFLINE.value: BearerMetrics(
                    available=True,
                    latency_ms=0.0,
                    jitter_ms=0.0,
                    loss_pct=0.0,
                    cost_per_mb=0.0,
                    energy_mw=1.0,
                    security_score=1.0,
                    user_preference=0.1,
                ),
            }

    def claim_boundary(self) -> str:
        return CLAIM_BOUNDARY

    def on_transition(self, listener: Callable[[TransitionRecord], None]) -> None:
        self._listeners.append(listener)

    def inject_fault(self, fault: str) -> None:
        """Fault-injection surface for tests (no physical radio control)."""
        self.faults.add(fault)
        if fault == "drop_active" and self.active_bearer != BearerKind.OFFLINE:
            key = self.active_bearer.value
            m = self.metrics[key]
            m.available = False
            m.loss_pct = 100.0
        elif fault == "inflate_latency" and self.active_bearer != BearerKind.OFFLINE:
            self.metrics[self.active_bearer.value].latency_ms = 5000.0
        elif fault == "jam_wifi":
            wifi = self.metrics[BearerKind.WIFI.value]
            wifi.available = False
            wifi.loss_pct = 100.0
        elif fault == "force_offline":
            for kind in (BearerKind.ETHERNET, BearerKind.WIFI, BearerKind.CELLULAR):
                self.metrics[kind.value].available = False
                self.metrics[kind.value].loss_pct = 100.0

    def clear_faults(self) -> None:
        self.faults.clear()

    def update_metrics(self, bearer: str | BearerKind, metrics: BearerMetrics) -> None:
        key = bearer.value if isinstance(bearer, BearerKind) else bearer
        if key not in self.metrics:
            raise ValueError(f"unknown bearer: {key}")
        if key == BearerKind.OFFLINE.value:
            # Offline path is always "available" as a fallback sink.
            metrics.available = True
        self.metrics[key] = metrics

    def score(self, bearer: str | BearerKind) -> float:
        key = bearer.value if isinstance(bearer, BearerKind) else bearer
        m = self.metrics[key]
        w = self.weights
        if not m.available:
            return float("-inf")
        if key == BearerKind.OFFLINE.value:
            # Prefer any real bearer when available; offline is last resort.
            return -1000.0 + (w.user_preference * m.user_preference * 10.0)

        signal_norm = 0.0
        if m.signal_dbm is not None:
            # Map typical -90..-30 dBm into 0..1
            signal_norm = max(0.0, min(1.0, (m.signal_dbm + 90.0) / 60.0))

        latency_term = max(0.0, 200.0 - m.latency_ms) / 200.0
        jitter_term = max(0.0, 50.0 - m.jitter_ms) / 50.0
        loss_term = max(0.0, 1.0 - (m.loss_pct / 100.0))
        cost_term = max(0.0, 1.0 - min(1.0, m.cost_per_mb))
        energy_term = max(0.0, 1.0 - min(1.0, m.energy_mw / 2000.0))

        return (
            w.availability * 1.0
            + w.signal * signal_norm * 10.0
            + w.latency * latency_term * 10.0
            + w.jitter * jitter_term * 10.0
            + w.loss * loss_term * 10.0
            + w.cost * cost_term * 10.0
            + w.energy * energy_term * 10.0
            + w.security * m.security_score * 10.0
            + w.user_preference * m.user_preference * 10.0
        )

    def rank_bearers(self) -> list[tuple[str, float]]:
        ranked = [(k, self.score(k)) for k in self.metrics]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    def evaluate(self) -> dict[str, Any]:
        self.state = OrchestratorState.EVALUATING
        ranked = self.rank_bearers()
        best_name, best_score = ranked[0]
        active_name = self.active_bearer.value
        active_score = self.score(active_name)

        should_switch = False
        reason = "hold"
        if best_name != active_name:
            if active_score == float("-inf") or not self.metrics[active_name].available:
                should_switch = True
                reason = "active_unavailable"
            elif best_score >= active_score + self.hysteresis:
                should_switch = True
                reason = "better_score"

        result = {
            "state": self.state.value,
            "ranked": [{"bearer": n, "score": s} for n, s in ranked],
            "active": active_name,
            "candidate": best_name,
            "should_switch": should_switch,
            "reason": reason,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }

        if should_switch:
            self.transition_to(BearerKind(best_name), reason=reason)
        elif active_name == BearerKind.OFFLINE.value or not self.metrics[active_name].available:
            self.state = OrchestratorState.OFFLINE
            self.active_bearer = BearerKind.OFFLINE
        elif best_score < 20.0 and active_name != BearerKind.OFFLINE.value:
            self.state = OrchestratorState.DEGRADED
        else:
            self.state = OrchestratorState.CONNECTED

        result["state"] = self.state.value
        result["active"] = self.active_bearer.value
        return result

    def transition_to(self, bearer: BearerKind | str, *, reason: str) -> TransitionRecord:
        target = bearer if isinstance(bearer, BearerKind) else BearerKind(bearer)
        before = self.state
        self.state = OrchestratorState.TRANSITIONING
        from_bearer = self.active_bearer
        from_score = self.score(from_bearer)
        to_score = self.score(target)
        self.active_bearer = target
        if target == BearerKind.OFFLINE:
            after = OrchestratorState.OFFLINE
        elif to_score < 20.0:
            after = OrchestratorState.DEGRADED
        else:
            after = OrchestratorState.CONNECTED
        self.state = after
        record = TransitionRecord(
            from_bearer=from_bearer.value,
            to_bearer=target.value,
            reason=reason,
            from_score=from_score,
            to_score=to_score,
            state_before=before.value,
            state_after=after.value,
        )
        self.history.append(record)
        for listener in self._listeners:
            listener(record)
        return record

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "active_bearer": self.active_bearer.value,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "ranked": self.rank_bearers(),
            "history": [asdict(h) for h in self.history],
            "faults": sorted(self.faults),
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }
