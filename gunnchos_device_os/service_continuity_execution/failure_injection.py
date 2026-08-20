"""Failure injection suite for continuity plane."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.models import CostClass, TrustLevel
from gunnchos_device_os.service_continuity_execution.models import ContinuityState
from gunnchos_device_os.service_continuity_execution.transition import digital_bearer_transition


def _c(cid: str, *, avail: bool, trust: TrustLevel = TrustLevel.TRUSTED, lat: float = 20.0) -> CandidatePath:
    now = 1_700_000_000.0
    return CandidatePath(
        candidate_id=cid,
        bearer_class="wifi" if "wifi" in cid else "cellular_generic",
        availability=avail,
        signal_quality=0.9 if avail else 0.0,
        latency_ms=lat,
        jitter_ms=3.0,
        packet_loss_ratio=0.01 if avail else 1.0,
        monetary_cost=0.0,
        cost_class=CostClass.UNMETERED,
        energy_cost=200.0,
        security_trust=trust,
        data_unlimited=True,
        application_compatibility=True,
        telemetry_timestamp=now - 1.0,
        telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
        confidence=0.9,
    )


def run_failure_injection_suite() -> dict[str, Any]:
    cases: dict[str, Any] = {}

    # all paths down
    all_down = digital_bearer_transition(from_bearer="wifi", candidates=[_c("wifi", avail=False), _c("cell", avail=False)])
    cases["all_paths_down"] = {
        "ok": all_down.continuity_state in (ContinuityState.FAILED, ContinuityState.OFFLINE)
        and all_down.seamless_digital is False,
        "result": all_down.to_dict(),
    }

    # untrusted fast path rejected by Wave005 hard gate via transition decide
    hostile = digital_bearer_transition(
        from_bearer="offline",
        candidates=[
            _c("hostile", avail=True, trust=TrustLevel.UNTRUSTED, lat=1.0),
            _c("wifi-safe", avail=True, trust=TrustLevel.TRUSTED, lat=30.0),
        ],
    )
    cases["untrusted_not_selected_over_trusted"] = {
        "ok": hostile.selected_candidate == "wifi-safe",
        "result": hostile.to_dict(),
    }

    # empty candidate list
    empty = digital_bearer_transition(from_bearer="wifi", candidates=[])
    cases["empty_candidates"] = {
        "ok": empty.continuity_state in (ContinuityState.FAILED, ContinuityState.OFFLINE) and empty.seamless_digital is False,
        "result": empty.to_dict(),
    }

    ok = all(c["ok"] for c in cases.values())
    return {
        "schema": "gunnchos.engineering_wave006.failure_injection.v1",
        "ok": ok,
        "cases": cases,
    }
