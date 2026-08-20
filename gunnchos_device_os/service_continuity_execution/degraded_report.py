"""NET-ORCH-035 — transparent degraded-mode reporting."""
from __future__ import annotations

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
    active_bearer: str | None,
    adaptation_mode: AdaptationMode,
    limitations: list[str] | None = None,
) -> DegradedModeReport:
    limitations = list(limitations or [])
    if continuity_state == ContinuityState.HEALTHY:
        msg = "Service is operating normally."
    elif continuity_state == ContinuityState.DEGRADED:
        msg = "Service is degraded; some features are limited."
    elif continuity_state == ContinuityState.TRANSITIONING:
        msg = "Switching network path; brief interruption possible."
    elif continuity_state == ContinuityState.RESUMING:
        msg = "Resuming your session from the last checkpoint."
    elif continuity_state == ContinuityState.OFFLINE:
        msg = "Offline mode: using local cache only."
    else:
        msg = "Service unavailable; retry when a path is available."
    if adaptation_mode == AdaptationMode.LOW_BANDWIDTH and "low_bandwidth" not in limitations:
        limitations.append("low_bandwidth")
    if adaptation_mode == AdaptationMode.EMERGENCY_MINIMAL and "emergency_minimal" not in limitations:
        limitations.append("emergency_minimal")
    return DegradedModeReport(
        continuity_state=continuity_state,
        active_bearer=active_bearer,
        adaptation_mode=adaptation_mode,
        limitations=limitations,
        user_visible_message=msg,
        claim_boundaries=dict(CLAIM_BOUNDARIES),
        transparent=True,
    )


def prove_degraded_mode_reporting() -> dict[str, Any]:
    healthy = build_degraded_report(
        continuity_state=ContinuityState.HEALTHY,
        active_bearer="wifi",
        adaptation_mode=AdaptationMode.FULL,
    )
    degraded = build_degraded_report(
        continuity_state=ContinuityState.DEGRADED,
        active_bearer="cellular",
        adaptation_mode=AdaptationMode.LOW_BANDWIDTH,
        limitations=["metered"],
    )
    offline = build_degraded_report(
        continuity_state=ContinuityState.OFFLINE,
        active_bearer=None,
        adaptation_mode=AdaptationMode.OFFLINE,
    )
    ok = (
        healthy.transparent is True
        and degraded.transparent is True
        and "low_bandwidth" in degraded.limitations
        and "metered" in degraded.limitations
        and offline.user_visible_message.startswith("Offline")
        and all(v is False for v in degraded.claim_boundaries.values())
        and degraded.to_dict()["continuity_state"] == "DEGRADED"
    )
    return {
        "schema": "gunnchos.engineering_wave006.degraded_mode_reporting.v1",
        "ok": ok,
        "healthy": healthy.to_dict(),
        "degraded": degraded.to_dict(),
        "offline": offline.to_dict(),
    }
