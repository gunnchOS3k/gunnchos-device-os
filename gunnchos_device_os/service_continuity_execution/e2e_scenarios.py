"""E2E scenarios A–J for Wave006 continuity plane."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.models import CostClass, ServiceClass, TrustLevel
from gunnchos_device_os.service_continuity_execution.adaptation import prove_low_bandwidth_adaptation
from gunnchos_device_os.service_continuity_execution.cache import prove_persistent_cache_a_b_c
from gunnchos_device_os.service_continuity_execution.controller import ContinuityController
from gunnchos_device_os.service_continuity_execution.degraded_report import prove_degraded_mode_reporting
from gunnchos_device_os.service_continuity_execution.local_infra import prove_local_infrastructure
from gunnchos_device_os.service_continuity_execution.models import BearerClass, ContinuityState, ServiceSession
from gunnchos_device_os.service_continuity_execution.multipath import prove_application_multipath
from gunnchos_device_os.service_continuity_execution.prioritization import prove_traffic_prioritization
from gunnchos_device_os.service_continuity_execution.resume import prove_session_resume_a_b_c
from gunnchos_device_os.service_continuity_execution.satellite import prove_satellite_visibility
from gunnchos_device_os.service_continuity_execution.sync import prove_opportunistic_sync
from gunnchos_device_os.service_continuity_execution.transition import prove_digital_bearer_transition


def _cand(cid: str, bearer: str, *, avail: bool = True, lat: float = 20.0, trust: TrustLevel = TrustLevel.TRUSTED) -> CandidatePath:
    now = 1_700_000_000.0
    return CandidatePath(
        candidate_id=cid,
        bearer_class=bearer,
        availability=avail,
        signal_quality=0.85 if avail else 0.0,
        latency_ms=lat,
        jitter_ms=3.0,
        packet_loss_ratio=0.005 if avail else 1.0,
        monetary_cost=0.0,
        cost_class=CostClass.UNMETERED,
        energy_cost=250.0,
        security_trust=trust,
        data_unlimited=True,
        application_compatibility=True,
        telemetry_timestamp=now - 1.0,
        telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
        confidence=0.9,
    )


def _scenario_a() -> dict[str, Any]:
    return prove_satellite_visibility()


def _scenario_b() -> dict[str, Any]:
    return prove_local_infrastructure()


def _scenario_c() -> dict[str, Any]:
    return prove_digital_bearer_transition()


def _scenario_d(tmp: Path) -> dict[str, Any]:
    return prove_session_resume_a_b_c(tmp / "resume")


def _scenario_e() -> dict[str, Any]:
    return prove_application_multipath()


def _scenario_f() -> dict[str, Any]:
    return prove_low_bandwidth_adaptation()


def _scenario_g() -> dict[str, Any]:
    return prove_traffic_prioritization()


def _scenario_h(tmp: Path) -> dict[str, Any]:
    return prove_persistent_cache_a_b_c(tmp / "cache")


def _scenario_i(tmp: Path) -> dict[str, Any]:
    return prove_opportunistic_sync(tmp / "sync")


def _scenario_j(tmp: Path) -> dict[str, Any]:
    ctrl = ContinuityController(storage_dir=tmp / "ctrl")
    out = ctrl.ingest_and_decide(
        [_cand("wifi", "wifi", avail=False), _cand("cell", "cellular", avail=True, lat=45.0)],
        service=ServiceClass.LEARNING,
        available_kbps=18.0,
        satellite_elevation_deg=40.0,
        satellites_in_view=3,
        gateway_reachable=True,
        dns_resolvable=True,
    )
    sess = ServiceSession(
        session_id="e2e-j",
        service_name="learning",
        bearer=BearerClass.CELLULAR,
        checkpoint={"cursor": 7},
    )
    ctrl.checkpoint_session(sess)
    # fresh controller instance = fresh process analogue
    ctrl2 = ContinuityController(storage_dir=tmp / "ctrl")
    resumed = ctrl2.resume_from_storage()
    report = prove_degraded_mode_reporting()
    shell = ctrl2.shell_view()
    ok = (
        out["satellite"]["visible"] is True
        and out["continuity_state"] in {s.value for s in ContinuityState}
        and resumed.checkpoint.get("cursor") == 7
        and resumed.checkpoint.get("resumed") is True
        and report["ok"] is True
        and shell["continuity_state"] == ContinuityState.RESUMING.value
        and out["claim_boundaries"]["LIVE_CARRIER_HANDOVER_VALIDATED"] is False
    )
    return {
        "schema": "gunnchos.engineering_wave006.e2e_scenario_j.v1",
        "ok": ok,
        "controller_out_state": out["continuity_state"],
        "resumed_cursor": resumed.checkpoint.get("cursor"),
        "shell": shell,
        "degraded_reporting_ok": report["ok"],
    }


def run_e2e_scenarios_a_through_j(tmp_dir: Path | None = None) -> dict[str, Any]:
    own = tmp_dir is None
    base = Path(tmp_dir) if tmp_dir else Path(tempfile.mkdtemp(prefix="wave006-e2e-"))
    base.mkdir(parents=True, exist_ok=True)
    runners: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("A_satellite_visibility", _scenario_a),
        ("B_local_infra", _scenario_b),
        ("C_bearer_transition", _scenario_c),
        ("D_session_resume", lambda: _scenario_d(base)),
        ("E_multipath", _scenario_e),
        ("F_low_bandwidth", _scenario_f),
        ("G_prioritization", _scenario_g),
        ("H_persistent_cache", lambda: _scenario_h(base)),
        ("I_opportunistic_sync", lambda: _scenario_i(base)),
        ("J_unified_controller", lambda: _scenario_j(base)),
    ]
    results: dict[str, Any] = {}
    passed = 0
    for name, fn in runners:
        row = fn()
        results[name] = row
        if row.get("ok") is True:
            passed += 1
    return {
        "schema": "gunnchos.engineering_wave006.e2e_scenarios_a_j.v1",
        "ok": passed == 10,
        "passed": passed,
        "total": 10,
        "scenarios": results,
        "temp_owned": own,
    }
