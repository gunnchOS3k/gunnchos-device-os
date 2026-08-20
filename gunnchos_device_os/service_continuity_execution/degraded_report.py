"""NET-ORCH-035 — canonical degraded-mode report + shell projection."""
from __future__ import annotations

import uuid
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import (
    AdaptationMode,
    CLAIM_BOUNDARIES,
    ContinuityState,
    DegradedModeReport,
)


def build_degraded_report(
    *,
    continuity_state: ContinuityState,
    active_bearer: str | None = None,
    adaptation_mode: AdaptationMode | str | None = None,
    limitations: list[str] | None = None,
    service_id: str = "svc-default",
    service_class: str = "communication",
    selected_paths: list[str] | None = None,
    reason_codes: list[str] | None = None,
    session_resume_available: bool = False,
    cache_available: bool = False,
    sync_deferred: bool = False,
    pending_sync_items: int = 0,
    data_cost_warning: str | None = None,
    security_warning: str | None = None,
    provenance: str = "HOST_OBSERVED_DIGITAL",
    timestamp: float = 1_700_000_000.0,
    internet_available: bool = True,
    local_edge: bool = False,
    local_cache: bool = False,
    local_peer: bool = False,
) -> DegradedModeReport:
    state = continuity_state
    adapt = adaptation_mode.value if isinstance(adaptation_mode, AdaptationMode) else (adaptation_mode or "FULL")
    paths = selected_paths or ([active_bearer] if active_bearer else [])

    retained: list[str] = []
    lost: list[str] = []
    if internet_available and state not in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.FAILED):
        retained.append("INTERNET_SERVICE")
    else:
        lost.append("INTERNET_SERVICE")
    if local_edge or cache_available:
        retained.append("LOCAL_EDGE_OR_CACHE")
    if local_cache or cache_available:
        retained.append("LOCAL_CACHE_SERVICE")
    else:
        if state in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.REDUCED_SERVICE, ContinuityState.FAILED):
            lost.append("CLOUD_SYNC")
    if local_peer:
        retained.append("LOCAL_PEER_SERVICE")
    if session_resume_available:
        retained.append("SESSION_RESUME")
    if state == ContinuityState.FAILED and not retained:
        lost.extend(["INTERACTIVE_SERVICE", "SYNC"])

    # Derive capability claims from runtime flags only
    if not cache_available and "LOCAL_CACHE_SERVICE" in retained:
        retained = [c for c in retained if c != "LOCAL_CACHE_SERVICE"]

    recovery = {
        ContinuityState.HEALTHY: "none",
        ContinuityState.DEGRADING: "bandwidth recovery",
        ContinuityState.TRANSITION_PREP: "complete transition preflight",
        ContinuityState.TRANSITIONING: "commit digital transition",
        ContinuityState.RESUMING: "finish resume ledger",
        ContinuityState.MULTIPATH: "complete multipath transfer",
        ContinuityState.REDUCED_SERVICE: "restore capacity above recovery threshold",
        ContinuityState.OFFLINE_CAPABLE: "restore path or use local cache/peer",
        ContinuityState.RECOVERING: "complete recovery to HEALTHY",
        ContinuityState.FAILED: "manual recover / resume from checkpoint",
    }.get(state, "unknown")

    limitations = list(limitations or [])
    if sync_deferred or pending_sync_items:
        limitations.append(f"sync_deferred:{pending_sync_items}")
    if not internet_available:
        limitations.append("internet_unavailable")

    msg = {
        ContinuityState.HEALTHY: "Service healthy",
        ContinuityState.REDUCED_SERVICE: "Service reduced — local work may continue",
        ContinuityState.OFFLINE_CAPABLE: "Offline-capable mode — cached work available",
        ContinuityState.FAILED: "Service failed — resume when path returns",
        ContinuityState.TRANSITIONING: "Transitioning bearers",
        ContinuityState.RESUMING: "Resuming session",
        ContinuityState.RECOVERING: "Recovering service",
        ContinuityState.MULTIPATH: "Multipath transfer in progress",
        ContinuityState.DEGRADING: "Service degrading",
        ContinuityState.TRANSITION_PREP: "Preparing transition",
    }.get(state, "Service status update")

    return DegradedModeReport(
        report_id=f"rpt-{uuid.uuid4().hex[:10]}",
        service_id=service_id,
        service_class=service_class,
        state=state,
        selected_paths=paths,
        reason_codes=list(reason_codes or [state.value]),
        lost_capabilities=lost,
        retained_capabilities=retained,
        current_adaptation_profile=adapt,
        session_resume_available=session_resume_available,
        cache_available=cache_available,
        sync_deferred=sync_deferred,
        pending_sync_items=pending_sync_items,
        estimated_recovery_condition=recovery,
        data_cost_warning=data_cost_warning,
        security_warning=security_warning,
        provenance=provenance,
        timestamp=timestamp,
        continuity_state=state,
        active_bearer=active_bearer,
        adaptation_mode=AdaptationMode(adapt) if adapt in AdaptationMode.__members__ or adapt in {m.value for m in AdaptationMode} else None,
        limitations=limitations,
        user_visible_message=msg,
        claim_boundaries=dict(CLAIM_BOUNDARIES),
    )


def prove_degraded_mode_reporting() -> dict[str, Any]:
    examples = {}
    for state in (
        ContinuityState.HEALTHY,
        ContinuityState.TRANSITIONING,
        ContinuityState.RESUMING,
        ContinuityState.REDUCED_SERVICE,
        ContinuityState.OFFLINE_CAPABLE,
        ContinuityState.FAILED,
        ContinuityState.RECOVERING,
    ):
        examples[state.value] = build_degraded_report(
            continuity_state=state,
            active_bearer="wifi" if state != ContinuityState.OFFLINE_CAPABLE else None,
            adaptation_mode=AdaptationMode.FULL if state == ContinuityState.HEALTHY else AdaptationMode.REDUCED,
            cache_available=state in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.REDUCED_SERVICE, ContinuityState.HEALTHY),
            session_resume_available=state in (ContinuityState.RESUMING, ContinuityState.OFFLINE_CAPABLE, ContinuityState.FAILED),
            sync_deferred=state in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.REDUCED_SERVICE),
            pending_sync_items=2 if state != ContinuityState.HEALTHY else 0,
            internet_available=state not in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.FAILED),
            local_cache=state in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.REDUCED_SERVICE),
            timestamp=1_700_000_600.0,
        ).to_dict()

    # runtime consistency: must not claim cache when missing
    bad_claim_prevented = build_degraded_report(
        continuity_state=ContinuityState.OFFLINE_CAPABLE,
        cache_available=False,
        internet_available=False,
    )
    consistent = "LOCAL_CACHE_SERVICE" not in bad_claim_prevented.retained_capabilities

    required_fields = [
        "report_id",
        "service_id",
        "service_class",
        "state",
        "selected_paths",
        "reason_codes",
        "lost_capabilities",
        "retained_capabilities",
        "current_adaptation_profile",
        "session_resume_available",
        "cache_available",
        "sync_deferred",
        "pending_sync_items",
        "estimated_recovery_condition",
        "data_cost_warning",
        "security_warning",
        "provenance",
        "timestamp",
        "shell_projection",
    ]
    sample = examples[ContinuityState.OFFLINE_CAPABLE.value]
    shell = sample["shell_projection"]
    checks = {
        "all_example_states": len(examples) == 7,
        "required_fields": all(f in sample for f in required_fields),
        "shell_projection_present": all(
            k in shell
            for k in (
                "headline",
                "what_still_works",
                "what_temporarily_unavailable",
                "work_safe_locally",
                "changes_pending_sync",
                "recovery_condition",
            )
        ),
        "runtime_consistent": consistent,
        "healthy_no_lost_internet": "INTERNET_SERVICE" in examples[ContinuityState.HEALTHY.value]["retained_capabilities"],
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.degraded_mode_reporting.v1",
        "ok": ok,
        "checks": checks,
        "examples": examples,
        "DEGRADED_REPORT_CANONICAL": True,
        "DEGRADED_REPORT_RUNTIME_CONSISTENT": consistent,
    }
