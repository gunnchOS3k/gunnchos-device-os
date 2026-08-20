"""NET-ORCH-028 — digital bearer transition (not live carrier handover)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.models import CostClass, ServiceClass, TrustLevel, default_objective_for
from gunnchos_device_os.service_continuity_execution.models import BearerClass, ContinuityState


@dataclass
class BearerTransitionResult:
    from_bearer: str
    to_bearer: str
    seamless_digital: bool
    continuity_state: ContinuityState
    selected_candidate: str | None
    LIVE_CARRIER_HANDOVER_VALIDATED: bool = False
    note: str = "software path reassignment only; not 3GPP/carrier handover"

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_bearer": self.from_bearer,
            "to_bearer": self.to_bearer,
            "seamless_digital": self.seamless_digital,
            "continuity_state": self.continuity_state.value,
            "selected_candidate": self.selected_candidate,
            "LIVE_CARRIER_HANDOVER_VALIDATED": False,
            "note": self.note,
        }


def _cand(cid: str, bearer: str, *, avail: bool, lat: float, trust: TrustLevel, now: float) -> CandidatePath:
    return CandidatePath(
        candidate_id=cid,
        bearer_class=bearer,
        availability=avail,
        signal_quality=0.8 if avail else 0.0,
        latency_ms=lat,
        jitter_ms=4.0,
        packet_loss_ratio=0.01 if avail else 1.0,
        monetary_cost=0.0 if bearer == "wifi" else 0.05,
        cost_class=CostClass.UNMETERED if bearer == "wifi" else CostClass.METERED,
        energy_cost=300.0,
        security_trust=trust,
        data_unlimited=True,
        application_compatibility=True,
        telemetry_timestamp=now - 1.0,
        telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
        confidence=0.9 if avail else 0.2,
    )


def digital_bearer_transition(
    *,
    from_bearer: str,
    candidates: list[CandidatePath],
    now: float = 1_700_000_000.0,
) -> BearerTransitionResult:
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: now)
    decision = eng.decide(candidates, default_objective_for(ServiceClass.COMMUNICATION))
    selected = decision.selected_candidate
    if selected is None:
        return BearerTransitionResult(
            from_bearer=from_bearer,
            to_bearer=BearerClass.OFFLINE.value,
            seamless_digital=False,
            continuity_state=ContinuityState.FAILED,
            selected_candidate=None,
        )
    bearer_norm = str(selected).lower()
    offline_like = bearer_norm in {"offline", "offline-fallback"} or bearer_norm.endswith("offline")
    if offline_like:
        return BearerTransitionResult(
            from_bearer=from_bearer,
            to_bearer=selected,
            seamless_digital=False,
            continuity_state=ContinuityState.OFFLINE,
            selected_candidate=selected,
            note="no admissible live path; digital offline fallback only",
        )
    seamless = selected != from_bearer and decision.service_floor not in ("UNAVAILABLE",)
    state = ContinuityState.TRANSITIONING if seamless else ContinuityState.DEGRADED
    if selected == from_bearer:
        state = ContinuityState.HEALTHY
        seamless = False
    return BearerTransitionResult(
        from_bearer=from_bearer,
        to_bearer=selected,
        seamless_digital=seamless,
        continuity_state=state,
        selected_candidate=selected,
    )


def prove_digital_bearer_transition() -> dict[str, Any]:
    now = 1_700_000_000.0
    # wifi drops → cellular digital path selected
    cands = [
        _cand("wifi", "wifi", avail=False, lat=999.0, trust=TrustLevel.TRUSTED, now=now),
        _cand("cell", "cellular", avail=True, lat=40.0, trust=TrustLevel.TRUSTED, now=now),
    ]
    tr = digital_bearer_transition(from_bearer="wifi", candidates=cands, now=now)
    # no candidates → failed/offline
    empty = digital_bearer_transition(from_bearer="wifi", candidates=[], now=now)
    ok = (
        tr.seamless_digital is True
        and tr.to_bearer == "cell"
        and tr.LIVE_CARRIER_HANDOVER_VALIDATED is False
        and empty.continuity_state in (ContinuityState.FAILED, ContinuityState.OFFLINE)
        and empty.seamless_digital is False
        and empty.selected_candidate in (None, "offline", "offline-fallback")
    )
    return {
        "schema": "gunnchos.engineering_wave006.bearer_transition.v1",
        "ok": ok,
        "wifi_to_cellular": tr.to_dict(),
        "no_candidates": empty.to_dict(),
        "LIVE_CARRIER_HANDOVER_VALIDATED": False,
    }
