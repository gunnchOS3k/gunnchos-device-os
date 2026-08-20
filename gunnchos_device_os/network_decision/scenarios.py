"""Service-continuity scenarios A–J (DIGITAL_SYNTHETIC_EVIDENCE)."""
from __future__ import annotations

import time
from typing import Any, Callable

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.models import (
    AnywhereServiceObjective,
    ApplicationPriority,
    CostClass,
    ServiceClass,
    TrustLevel,
    UserPreferenceProfile,
    default_objective_for,
)

NOW = 1_700_000_000.0


def _base_wifi(**kw: Any) -> CandidatePath:
    d = dict(
        candidate_id="wifi-home",
        bearer_class="wifi",
        availability=True,
        signal_quality=0.85,
        signal_raw={"rssi_dbm": -45},
        latency_ms=20.0,
        jitter_ms=4.0,
        packet_loss_ratio=0.005,
        monetary_cost=0.0,
        cost_class=CostClass.UNMETERED,
        energy_cost=350.0,
        security_trust=TrustLevel.TRUSTED,
        data_unlimited=True,
        application_compatibility=True,
        telemetry_timestamp=NOW - 1.0,
        telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
        confidence=0.95,
    )
    d.update(kw)
    return CandidatePath(**d)


def _base_cell(**kw: Any) -> CandidatePath:
    d = dict(
        candidate_id="cell-generic",
        bearer_class="cellular_generic",
        availability=True,
        signal_quality=0.7,
        signal_raw={"rsrp_dbm": -95},
        latency_ms=45.0,
        jitter_ms=12.0,
        packet_loss_ratio=0.01,
        monetary_cost=0.05,
        cost_class=CostClass.METERED,
        energy_cost=900.0,
        security_trust=TrustLevel.TRUSTED,
        data_metered=True,
        data_remaining_fraction=0.6,
        application_compatibility=True,
        telemetry_timestamp=NOW - 1.0,
        telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
        confidence=0.9,
    )
    d.update(kw)
    return CandidatePath(**d)


def scenario_a() -> dict[str, Any]:
    """Strong trusted Wi-Fi vs costly cellular → prefer Wi-Fi."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    d = eng.decide([_base_wifi(), _base_cell(monetary_cost=0.2, cost_class=CostClass.ROAMING_HIGH, roaming_high_cost=True)], obj)
    ok = d.selected_candidate == "wifi-home"
    return {"id": "A", "ok": ok, "expected": "wifi-home", "selected": d.selected_candidate, "explanation": d.to_dict()}


def scenario_b() -> dict[str, Any]:
    """Wi-Fi quality collapses → cellular."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.COMMUNICATION)
    wifi = _base_wifi(signal_quality=0.1, latency_ms=400.0, jitter_ms=90.0, packet_loss_ratio=0.2)
    d = eng.decide([wifi, _base_cell()], obj)
    ok = d.selected_candidate == "cell-generic"
    return {"id": "B", "ok": ok, "expected": "cell-generic", "selected": d.selected_candidate, "explanation": d.to_dict()}


def scenario_c() -> dict[str, Any]:
    """Free but untrusted network must be rejected."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.constraints.min_trust = TrustLevel.TRUSTED
    hostile = _base_wifi(
        candidate_id="wifi-hostile-free",
        latency_ms=5.0,
        monetary_cost=0.0,
        cost_class=CostClass.UNMETERED,
        security_trust=TrustLevel.UNTRUSTED,
        energy_cost=100.0,
    )
    d = eng.decide([hostile, _base_cell()], obj)
    rejected_ids = [r["candidate_id"] for r in d.rejected_candidates]
    ok = "wifi-hostile-free" in rejected_ids and d.selected_candidate == "cell-generic"
    reasons = d.hard_constraint_reasons.get("wifi-hostile-free", [])
    ok = ok and "security_below_required_trust" in reasons
    return {"id": "C", "ok": ok, "expected": "reject_hostile_select_cell", "selected": d.selected_candidate, "explanation": d.to_dict()}


def scenario_d() -> dict[str, Any]:
    """Low battery → prefer lower energy."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.continuity.battery_saving = True
    obj.user_preference = UserPreferenceProfile.PREFER_BATTERY
    wifi = _base_wifi(energy_cost=300.0)
    cell = _base_cell(energy_cost=1200.0)
    d = eng.decide([wifi, cell], obj)
    ok = d.selected_candidate == "wifi-home"
    return {"id": "D", "ok": ok, "expected": "wifi-home", "selected": d.selected_candidate, "explanation": d.to_dict()}


def scenario_e() -> dict[str, Any]:
    """Metered/data-limited → prefer unmetered."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.BACKGROUND_SYNC)
    obj.user_preference = UserPreferenceProfile.PREFER_UNMETERED
    cell = _base_cell(data_remaining_fraction=0.05, data_hard_limit=True, data_metered=True)
    d = eng.decide([_base_wifi(), cell], obj)
    ok = d.selected_candidate == "wifi-home"
    return {"id": "E", "ok": ok, "expected": "wifi-home", "selected": d.selected_candidate, "explanation": d.to_dict()}


def scenario_f() -> dict[str, Any]:
    """High latency + high jitter on wifi → cell for communication."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.COMMUNICATION)
    wifi = _base_wifi(latency_ms=250.0, jitter_ms=80.0)
    d = eng.decide([wifi, _base_cell(latency_ms=40.0, jitter_ms=8.0)], obj)
    ok = d.selected_candidate == "cell-generic"
    return {"id": "F", "ok": ok, "expected": "cell-generic", "selected": d.selected_candidate, "explanation": d.to_dict()}


def scenario_g() -> dict[str, Any]:
    """All online candidates unusable → offline/degraded."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    wifi = _base_wifi(availability=False)
    cell = _base_cell(availability=False)
    d = eng.decide([wifi, cell], obj)
    ok = d.service_floor in {"OFFLINE_CAPABLE", "UNAVAILABLE"} and (
        d.selected_candidate in {None, "offline-fallback"} or (d.selected_candidate or "").startswith("offline")
    )
    return {"id": "G", "ok": ok, "expected": "offline_or_unavailable", "selected": d.selected_candidate, "floor": d.service_floor, "explanation": d.to_dict()}


def scenario_h() -> dict[str, Any]:
    """Same telemetry, different user preference → different selection."""
    # Near-parity paths so preference dominates: wifi unmetered but hungry; cell cheaper-energy.
    cands = [
        _base_wifi(energy_cost=1500.0, monetary_cost=0.0, latency_ms=30.0, signal_quality=0.75),
        _base_cell(energy_cost=250.0, monetary_cost=0.02, cost_class=CostClass.METERED, latency_ms=32.0, signal_quality=0.75, jitter_ms=5.0, packet_loss_ratio=0.008),
    ]
    eng1 = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj1 = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj1.user_preference = UserPreferenceProfile.PREFER_LOW_COST
    d1 = eng1.decide(cands, obj1)

    eng2 = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj2 = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj2.user_preference = UserPreferenceProfile.PREFER_BATTERY
    obj2.continuity.battery_saving = True
    d2 = eng2.decide(cands, obj2)
    ok = d1.selected_candidate == "wifi-home" and d2.selected_candidate == "cell-generic"
    return {
        "id": "H",
        "ok": ok,
        "expected": "wifi_for_cost_cell_for_battery",
        "selected_cost": d1.selected_candidate,
        "selected_battery": d2.selected_candidate,
        "explanation_cost": d1.to_dict(),
        "explanation_battery": d2.to_dict(),
    }


def scenario_i() -> dict[str, Any]:
    """Stale/invalid telemetry rejected safely."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    stale = _base_wifi(candidate_id="wifi-stale", telemetry_timestamp=NOW - 600.0)
    bad = _base_cell(candidate_id="cell-bad", latency_ms=-5.0)
    good = _base_wifi(candidate_id="wifi-fresh", telemetry_timestamp=NOW - 1.0)
    d = eng.decide([stale, bad, good], obj)
    rejected = {r["candidate_id"] for r in d.rejected_candidates}
    ok = "wifi-stale" in rejected and "cell-bad" in rejected and d.selected_candidate == "wifi-fresh"
    return {"id": "I", "ok": ok, "expected": "select_fresh_reject_stale_invalid", "selected": d.selected_candidate, "rejected": sorted(rejected), "explanation": d.to_dict()}


def scenario_j() -> dict[str, Any]:
    """Deterministic tie → stable bearer order + candidate_id."""
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    # Two wifi clones with identical metrics — tie break by candidate_id
    a = _base_wifi(candidate_id="wifi-a")
    b = _base_wifi(candidate_id="wifi-b")
    d1 = eng.decide([b, a], obj)  # insert order reversed
    d2 = eng.decide([a, b], obj)
    ok = d1.selected_candidate == d2.selected_candidate == "wifi-a" and d1.tie_break_reason is not None
    return {"id": "J", "ok": ok, "expected": "wifi-a", "selected": d1.selected_candidate, "tie": d1.tie_break_reason, "explanation": d1.to_dict()}


def scenario_k() -> dict[str, Any]:
    """Same telemetry, priority-only change → selection boundary."""
    from gunnchos_device_os.network_decision.priority_authority import prove_priority_only_boundary
    boundary = prove_priority_only_boundary()
    return {"id": "K", "ok": boundary.get("ok") is True, "expected": "priority_only_selection_change", "boundary": boundary}


def scenario_l() -> dict[str, Any]:
    """Self-asserted CRITICAL is rejected/downgraded."""
    from gunnchos_device_os.network_decision.models import PriorityAuthority, PrioritySource
    from gunnchos_device_os.network_decision.priority_authority import resolve_priority_authority
    res = resolve_priority_authority(
        ApplicationPriority.CRITICAL,
        PriorityAuthority(source=PrioritySource.APP_SELF_ASSERTED, trusted=False, asserted_priority=ApplicationPriority.CRITICAL),
    )
    ok = res["effective"] != "CRITICAL" and res["action"] == "downgraded"
    return {"id": "L", "ok": ok, "expected": "downgrade_self_asserted_critical", "resolved": res}


def scenario_m() -> dict[str, Any]:
    """HARD avoid_cellular prevents cellular selection."""
    import tempfile
    from pathlib import Path
    from gunnchos_device_os.network_decision.models import EnforcementMode, NetworkPreferencePolicy
    from gunnchos_device_os.network_decision.preferences import UserPreferenceStore
    with tempfile.TemporaryDirectory() as tmp:
        store = UserPreferenceStore(Path(tmp), profile_id="m")
        store.set_policy(NetworkPreferencePolicy(
            preference=UserPreferenceProfile.AVOID_CELLULAR,
            enforcement_mode=EnforcementMode.HARD,
            hard_avoid_bearers={"cellular_generic"},
            profile_id="m",
        ))
        eng = AnywhereNetworkDecisionEngine(preference_store=store, now_fn=lambda: NOW)
        obj = default_objective_for(ServiceClass.PRODUCTIVITY)
        d = eng.decide([_base_wifi(latency_ms=250.0), _base_cell(latency_ms=10.0)], obj)
        ok = d.selected_candidate == "wifi-home" and "cell-generic" in [r["candidate_id"] for r in d.rejected_candidates]
    return {"id": "M", "ok": ok, "expected": "hard_avoid_cellular", "selected": d.selected_candidate, "rejected": d.rejected_candidates}


def scenario_n() -> dict[str, Any]:
    """HARD avoid_metered prevents metered selection."""
    import tempfile
    from pathlib import Path
    from gunnchos_device_os.network_decision.models import EnforcementMode, NetworkPreferencePolicy
    from gunnchos_device_os.network_decision.preferences import UserPreferenceStore
    with tempfile.TemporaryDirectory() as tmp:
        store = UserPreferenceStore(Path(tmp), profile_id="n")
        store.set_policy(NetworkPreferencePolicy(
            preference=UserPreferenceProfile.AVOID_METERED,
            enforcement_mode=EnforcementMode.HARD,
            hard_avoid_metered=True,
            profile_id="n",
        ))
        eng = AnywhereNetworkDecisionEngine(preference_store=store, now_fn=lambda: NOW)
        obj = default_objective_for(ServiceClass.PRODUCTIVITY)
        d = eng.decide([_base_wifi(), _base_cell(latency_ms=5.0, signal_quality=0.99)], obj)
        ok = d.selected_candidate == "wifi-home" and "cell-generic" in [r["candidate_id"] for r in d.rejected_candidates]
    return {"id": "N", "ok": ok, "expected": "hard_avoid_metered", "selected": d.selected_candidate}


def scenario_o() -> dict[str, Any]:
    """Unknown cost/energy/latency never treated best-case."""
    from gunnchos_device_os.network_decision.invalid_telemetry import _prove_unknown_not_best
    proofs = _prove_unknown_not_best()
    return {"id": "O", "ok": proofs.get("ok") is True, "expected": "unknown_not_best_case", "proofs": proofs}


SCENARIOS: list[Callable[[], dict[str, Any]]] = [
    scenario_a, scenario_b, scenario_c, scenario_d, scenario_e,
    scenario_f, scenario_g, scenario_h, scenario_i, scenario_j,
    scenario_k, scenario_l, scenario_m, scenario_n, scenario_o,
]


def run_all_scenarios() -> dict[str, Any]:
    results = [fn() for fn in SCENARIOS]
    return {
        "schema": "gunnchos.engineering_wave005.service_continuity_scenarios.v1",
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
        "PHYSICAL_VALIDATION": False,
        "FIELD_MEASURED_PERFORMANCE": False,
        "count": len(results),
        "passed": sum(1 for r in results if r.get("ok")),
        "failed": [r["id"] for r in results if not r.get("ok")],
        "ok": all(r.get("ok") for r in results),
        "scenarios": results,
        "generated_at_unix": time.time(),
    }
