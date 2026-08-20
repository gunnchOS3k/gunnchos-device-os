"""Unified ContinuityController — telemetry → Wave005 decision → continuity actions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine, DecisionExplanation
from gunnchos_device_os.network_decision.models import ServiceClass, default_objective_for
from gunnchos_device_os.service_continuity_execution.adaptation import adapt_payload, select_adaptation_mode
from gunnchos_device_os.service_continuity_execution.cache import PersistentContinuityCache
from gunnchos_device_os.service_continuity_execution.degraded_report import build_degraded_report
from gunnchos_device_os.service_continuity_execution.local_infra import evaluate_local_infrastructure
from gunnchos_device_os.service_continuity_execution.models import (
    AdaptationMode,
    BearerClass,
    CLAIM_BOUNDARIES,
    ContinuityState,
    SatelliteVisibilityProvenance,
    ServiceSession,
)
from gunnchos_device_os.service_continuity_execution.multipath import build_multipath_plan, stripe_application_payload
from gunnchos_device_os.service_continuity_execution.resume import load_session_checkpoint, resume_session, save_session_checkpoint
from gunnchos_device_os.service_continuity_execution.satellite import evaluate_satellite_visibility
from gunnchos_device_os.service_continuity_execution.transition import digital_bearer_transition


@dataclass
class ContinuityController:
    """Single execution plane for NET-ORCH-026..035. Not a parallel demo orchestrator."""

    storage_dir: Path
    state: ContinuityState = ContinuityState.HEALTHY
    active_bearer: str | None = None
    adaptation_mode: AdaptationMode = AdaptationMode.FULL
    last_decision: DecisionExplanation | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    now: float = 1_700_000_000.0

    def __post_init__(self) -> None:
        self.storage_dir = Path(self.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache = PersistentContinuityCache(self.storage_dir / "cache.json")
        self._session_path = self.storage_dir / "session.json"

    def ingest_and_decide(
        self,
        candidates: list[CandidatePath],
        *,
        service: ServiceClass = ServiceClass.COMMUNICATION,
        available_kbps: float | None = 500.0,
        satellite_elevation_deg: float | None = None,
        satellites_in_view: int = 0,
        gateway_reachable: bool = True,
        dns_resolvable: bool = True,
    ) -> dict[str, Any]:
        sat = evaluate_satellite_visibility(
            elevation_deg=satellite_elevation_deg,
            satellites_in_view=satellites_in_view,
            provenance=SatelliteVisibilityProvenance.SIMULATED
            if satellite_elevation_deg is not None
            else SatelliteVisibilityProvenance.UNKNOWN,
        )
        infra = evaluate_local_infrastructure(
            gateway_reachable=gateway_reachable,
            dns_resolvable=dns_resolvable,
        )
        eng = AnywhereNetworkDecisionEngine(now_fn=lambda: self.now)
        decision = eng.decide(candidates, default_objective_for(service))
        self.last_decision = decision

        from_bearer = self.active_bearer or "offline"
        transition = digital_bearer_transition(from_bearer=from_bearer, candidates=candidates, now=self.now)
        self.active_bearer = transition.to_bearer if transition.selected_candidate else None

        self.adaptation_mode = select_adaptation_mode(
            available_kbps=available_kbps,
            emergency=(service == ServiceClass.EMERGENCY),
            offline=(self.active_bearer in (None, "offline")),
        )

        if transition.continuity_state == ContinuityState.FAILED or self.active_bearer in (None, "offline"):
            self.state = ContinuityState.OFFLINE if self.adaptation_mode == AdaptationMode.OFFLINE else ContinuityState.FAILED
        elif transition.seamless_digital:
            self.state = ContinuityState.TRANSITIONING
        elif self.adaptation_mode in (AdaptationMode.LOW_BANDWIDTH, AdaptationMode.REDUCED, AdaptationMode.EMERGENCY_MINIMAL):
            self.state = ContinuityState.DEGRADED
        else:
            self.state = ContinuityState.HEALTHY

        paths = [c.candidate_id for c in candidates if c.availability]
        mp = build_multipath_plan(paths, prefer=self.active_bearer)
        mp = stripe_application_payload(mp, b"payload-demo")

        report = build_degraded_report(
            continuity_state=self.state,
            active_bearer=self.active_bearer,
            adaptation_mode=self.adaptation_mode,
            limitations=[],
        )
        out = {
            "satellite": sat.to_dict(),
            "local_infra": infra.to_dict(),
            "decision": decision.to_dict() if decision else None,
            "transition": transition.to_dict(),
            "multipath": mp.to_dict(),
            "adaptation_mode": self.adaptation_mode.value,
            "continuity_state": self.state.value,
            "degraded_report": report.to_dict(),
            "claim_boundaries": dict(CLAIM_BOUNDARIES),
        }
        self.history.append({"event": "ingest_and_decide", "state": self.state.value})
        return out

    def checkpoint_session(self, session: ServiceSession) -> None:
        save_session_checkpoint(session, self._session_path)

    def resume_from_storage(self) -> ServiceSession:
        session = load_session_checkpoint(self._session_path)
        session = resume_session(session)
        self.state = ContinuityState.RESUMING
        save_session_checkpoint(session, self._session_path)
        return session

    def cache_put(self, key: str, value: Any) -> None:
        self.cache.put(key, value)

    def cache_get(self, key: str) -> Any:
        return self.cache.get(key)

    def shell_view(self) -> dict[str, Any]:
        report = build_degraded_report(
            continuity_state=self.state,
            active_bearer=self.active_bearer,
            adaptation_mode=self.adaptation_mode,
        )
        return {
            "schema": "gunnchos.engineering_wave006.shell_view.v1",
            "continuity_state": self.state.value,
            "active_bearer": self.active_bearer,
            "adaptation_mode": self.adaptation_mode.value,
            "user_message": report.user_visible_message,
            "limitations": report.limitations,
            "claim_boundaries": dict(CLAIM_BOUNDARIES),
        }
