"""Unified ContinuityController — executes KEEP/TRANSITION/RESUME/MULTIPATH/ADAPT/CACHE_ONLY/OPPORTUNISTIC_SYNC/RECOVER/FAIL."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.models import ServiceClass, default_objective_for
from gunnchos_device_os.service_continuity_execution.adaptation import AdaptationController, AdaptationPolicy
from gunnchos_device_os.service_continuity_execution.cache import PersistentContinuityCache
from gunnchos_device_os.service_continuity_execution.degraded_report import build_degraded_report
from gunnchos_device_os.service_continuity_execution.local_infra import evaluate_local_infrastructure
from gunnchos_device_os.service_continuity_execution.models import (
    AdaptationMode,
    CLAIM_BOUNDARIES,
    ContinuityAction,
    ContinuityState,
    SatelliteVisibilityProvenance,
    ServiceSession,
)
from gunnchos_device_os.service_continuity_execution.multipath import run_multipath_transfer
from gunnchos_device_os.service_continuity_execution.resume import checkpoint, create_session, load_checkpoint, resume_once
from gunnchos_device_os.service_continuity_execution.satellite import build_visibility_window
from gunnchos_device_os.service_continuity_execution.state_machine import try_transition
from gunnchos_device_os.service_continuity_execution.sync import SyncPlanner, make_opportunity
from gunnchos_device_os.service_continuity_execution.transition import execute_transition, plan_bearer_transition
from gunnchos_device_os.service_continuity_execution.models import ContinuityEvent


@dataclass
class ContinuityExecutionPlan:
    action: ContinuityAction
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action.value, "reason": self.reason, "details": self.details}


@dataclass
class ContinuityController:
    storage_dir: Path
    state: ContinuityState = ContinuityState.HEALTHY
    active_bearer: str | None = None
    adaptation_mode: AdaptationMode = AdaptationMode.FULL
    last_decision: Any = None
    history: list[dict[str, Any]] = field(default_factory=list)
    now: float = 1_700_000_000.0
    logical_session_id: str = "logical-sess-main"

    def __post_init__(self) -> None:
        self.storage_dir = Path(self.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache = PersistentContinuityCache(self.storage_dir / "cache.json")
        self._session_path = self.storage_dir / "session.json"
        self.adaptation = AdaptationController(policy=AdaptationPolicy())
        self.sync_planner = SyncPlanner()

    def _set_state(self, event: ContinuityEvent) -> dict[str, Any]:
        result = try_transition(self.state, event)
        if result["ok"]:
            self.state = ContinuityState(result["to"])
        return result

    def execute(self, action: ContinuityAction, **kwargs: Any) -> dict[str, Any]:
        plan = ContinuityExecutionPlan(action=action, reason=kwargs.get("reason", action.value))
        if action == ContinuityAction.KEEP:
            out = {"ok": True, "state": self.state.value}
        elif action == ContinuityAction.TRANSITION:
            out = self._do_transition(**kwargs)
        elif action == ContinuityAction.RESUME:
            out = self._do_resume(**kwargs)
        elif action == ContinuityAction.MULTIPATH:
            out = self._do_multipath(**kwargs)
        elif action == ContinuityAction.ADAPT:
            kbps = float(kwargs.get("available_kbps", 500))
            self.adaptation_mode = self.adaptation.observe(kbps)
            if self.adaptation_mode != AdaptationMode.FULL:
                self._set_state(ContinuityEvent.BANDWIDTH_DROP)
            out = {"ok": True, "mode": self.adaptation_mode.value, "history_tail": self.adaptation.history[-1]}
        elif action == ContinuityAction.CACHE_ONLY:
            self._set_state(ContinuityEvent.ENTER_OFFLINE)
            out = {"ok": True, "cache_keys": self.cache.list_namespace(kwargs.get("namespace", "default"))}
        elif action == ContinuityAction.OPPORTUNISTIC_SYNC:
            out = self._do_sync(**kwargs)
        elif action == ContinuityAction.RECOVER:
            self._set_state(ContinuityEvent.BEGIN_RECOVERY)
            self._set_state(ContinuityEvent.RECOVERY_DONE)
            self.adaptation_mode = AdaptationMode.FULL
            out = {"ok": True, "state": self.state.value}
        elif action == ContinuityAction.FAIL:
            self._set_state(ContinuityEvent.FAIL)
            out = {"ok": True, "state": self.state.value}
        else:
            out = {"ok": False, "reason": "unknown_action"}
        plan.details = out
        self.history.append(plan.to_dict())
        return {"plan": plan.to_dict(), "result": out, "state": self.state.value}

    def _do_transition(self, **kwargs: Any) -> dict[str, Any]:
        source = kwargs.get("source_path", self.active_bearer or "wifi")
        target = kwargs["target_path"]
        self._set_state(ContinuityEvent.BEGIN_TRANSITION)
        plan = plan_bearer_transition(
            source_path=source,
            target_path=target,
            logical_session_id=self.logical_session_id,
            now=self.now,
            target_available=kwargs.get("target_available", True),
            target_trust_ok=kwargs.get("target_trust_ok", True),
        )
        self._set_state(ContinuityEvent.TRANSITION_PREP_OK)
        execu = execute_transition(
            plan,
            now=self.now,
            force_activation_failure=kwargs.get("force_activation_failure", False),
            force_commit_failure=kwargs.get("force_commit_failure", False),
        )
        if execu.state.value == "COMMITTED":
            self.active_bearer = target
            self._set_state(ContinuityEvent.TRANSITION_COMMIT)
        elif execu.rollback_used:
            self._set_state(ContinuityEvent.TRANSITION_ROLLBACK)
        else:
            self._set_state(ContinuityEvent.FAIL)
        return execu.to_dict()

    def _do_resume(self, **kwargs: Any) -> dict[str, Any]:
        self._set_state(ContinuityEvent.BEGIN_RESUME)
        sess = load_checkpoint(self._session_path)
        sess, result = resume_once(sess, now=self.now, resume_token=kwargs.get("resume_token", sess.resume_token))
        checkpoint(sess, self._session_path, now=self.now)
        if result.get("ok"):
            self._set_state(ContinuityEvent.RESUME_DONE)
        else:
            self._set_state(ContinuityEvent.FAIL)
        return {"session": sess.to_dict(), "resume": result}

    def _do_multipath(self, **kwargs: Any) -> dict[str, Any]:
        self._set_state(ContinuityEvent.BEGIN_MULTIPATH)
        payload = kwargs.get("payload", b"controller-multipath-payload-bytes")
        paths = kwargs.get("paths", ["path-a", "path-b"])
        result = run_multipath_transfer(
            payload if isinstance(payload, (bytes, bytearray)) else str(payload).encode(),
            paths,
            fail_path=kwargs.get("fail_path"),
            inject_duplicate=kwargs.get("inject_duplicate", False),
            shuffle_delivery=kwargs.get("shuffle_delivery", True),
        )
        if result.get("ok"):
            self._set_state(ContinuityEvent.MULTIPATH_DONE)
        else:
            self._set_state(ContinuityEvent.FAIL)
        return result

    def _do_sync(self, **kwargs: Any) -> dict[str, Any]:
        opp = kwargs.get("opportunity") or make_opportunity(
            path_id=self.active_bearer or "wifi",
            path_class=kwargs.get("path_class", "terrestrial"),
            now=self.now,
            max_bytes=kwargs.get("max_bytes", 5000),
        )
        return self.sync_planner.plan_and_apply(opp, now=self.now)

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
        backhaul_reachable: bool = True,
        local_cache_available: bool = False,
    ) -> dict[str, Any]:
        sat = build_visibility_window(
            candidate_id="ntn-sim",
            elevation_deg=satellite_elevation_deg,
            satellites_in_view=satellites_in_view,
            window_start_utc=self.now - 5,
            window_end_utc=self.now + 60,
            observed_or_generated_at=self.now,
            provenance=SatelliteVisibilityProvenance.SIMULATED
            if satellite_elevation_deg is not None
            else SatelliteVisibilityProvenance.UNKNOWN,
        )
        infra = evaluate_local_infrastructure(
            gateway_reachable=gateway_reachable,
            dns_resolvable=dns_resolvable,
            backhaul_reachable=backhaul_reachable,
            local_cache_available=local_cache_available,
            observed_at=self.now,
        )
        eng = AnywhereNetworkDecisionEngine(now_fn=lambda: self.now)
        decision = eng.decide(candidates, default_objective_for(service))
        self.last_decision = decision

        from_bearer = self.active_bearer or "offline"
        target = decision.selected_candidate_id if decision else None
        if target and target != from_bearer:
            action_result = self.execute(
                ContinuityAction.TRANSITION,
                source_path=from_bearer,
                target_path=target,
                reason="wave005_selected_target",
            )
        elif available_kbps is not None and available_kbps < 200:
            action_result = self.execute(ContinuityAction.ADAPT, available_kbps=available_kbps)
        else:
            action_result = self.execute(ContinuityAction.KEEP)

        report = build_degraded_report(
            continuity_state=self.state,
            active_bearer=self.active_bearer,
            adaptation_mode=self.adaptation_mode,
            cache_available=local_cache_available or self.cache.list_namespace("default") != [],
            internet_available=infra.capabilities(self.now)["INTERNET_SERVICE"],
            local_cache=local_cache_available,
            timestamp=self.now,
        )
        out = {
            "satellite": sat.to_dict(),
            "local_infra": infra.to_dict(self.now),
            "decision": decision.to_dict() if decision else None,
            "action": action_result,
            "adaptation_mode": self.adaptation_mode.value,
            "continuity_state": self.state.value,
            "degraded_report": report.to_dict(),
            "claim_boundaries": dict(CLAIM_BOUNDARIES),
            "satellite_visible_now": sat.is_visible_now(self.now),
        }
        self.history.append({"event": "ingest_and_decide", "state": self.state.value})
        return out

    def checkpoint_session(self, session: ServiceSession | None = None) -> ServiceSession:
        sess = session or create_session(now=self.now)
        checkpoint(sess, self._session_path, now=self.now)
        return sess

    def resume_from_storage(self) -> ServiceSession:
        result = self.execute(ContinuityAction.RESUME)
        return load_checkpoint(self._session_path)

    def cache_put(self, key: str, value: Any, **kwargs: Any) -> None:
        self.cache.put(key, value, **kwargs)

    def cache_get(self, key: str, **kwargs: Any) -> Any:
        return self.cache.get(key, **kwargs)

    def shell_view(self) -> dict[str, Any]:
        report = build_degraded_report(
            continuity_state=self.state,
            active_bearer=self.active_bearer,
            adaptation_mode=self.adaptation_mode,
            cache_available=bool(self.cache.list_namespace("default")),
            timestamp=self.now,
        )
        return {
            "schema": "gunnchos.engineering_wave006.shell_view.v1",
            "continuity_state": self.state.value,
            "active_bearer": self.active_bearer,
            "adaptation_mode": self.adaptation_mode.value,
            "user_message": report.user_visible_message,
            "limitations": report.limitations,
            "shell_projection": report.to_dict()["shell_projection"],
            "claim_boundaries": dict(CLAIM_BOUNDARIES),
        }
