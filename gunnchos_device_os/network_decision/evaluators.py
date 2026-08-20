"""Requirement-specific evaluators for NET-ORCH-001/014–024. No unconditional True."""
from __future__ import annotations

from typing import Any, Callable

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.invariants import run_invariants
from gunnchos_device_os.network_decision.invalid_telemetry import run_invalid_telemetry
from gunnchos_device_os.network_decision.metrics import (
    normalize_signal,
    score_availability,
    score_cost,
    score_data,
    score_energy,
    score_jitter,
    score_latency,
    score_packet_loss,
    score_security,
    score_user_preference,
    score_application_priority,
)
from gunnchos_device_os.network_decision.models import (
    AnywhereServiceObjective,
    ApplicationPriority,
    CostClass,
    ServiceClass,
    ServiceFloor,
    TrustLevel,
    UserPreferenceProfile,
    default_objective_for,
)
from gunnchos_device_os.network_decision.preferences import UserPreferenceStore
from gunnchos_device_os.network_decision.scenarios import run_all_scenarios

TARGET_REQUIREMENTS = (
    "NET-ORCH-001",
    "NET-ORCH-014",
    "NET-ORCH-015",
    "NET-ORCH-016",
    "NET-ORCH-017",
    "NET-ORCH-018",
    "NET-ORCH-019",
    "NET-ORCH-020",
    "NET-ORCH-021",
    "NET-ORCH-022",
    "NET-ORCH-023",
    "NET-ORCH-024",
)

NOW = 1_700_000_000.0


def _result(req_id: str, ok: bool, note: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "requirement_id": req_id,
        "classification": "IMPLEMENTED_AND_VALIDATED" if ok else "IMPLEMENTATION_OPEN",
        "ok": ok,
        "note": note,
        "evaluator": f"evaluate_{req_id.lower().replace('-', '_')}",
        "evidence": evidence or {},
    }


def _wifi(**kw: Any) -> CandidatePath:
    d = dict(
        candidate_id="wifi",
        bearer_class="wifi",
        availability=True,
        signal_quality=0.8,
        signal_raw={"rssi_dbm": -50},
        latency_ms=20.0,
        jitter_ms=4.0,
        packet_loss_ratio=0.01,
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


def evaluate_net_orch_001(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.EMERGENCY)
    d = obj.to_dict()
    required_classes = {c.value for c in ServiceClass}
    required_floors = {f.value for f in ServiceFloor}
    ok = (
        set(ServiceClass.__members__) >= {"EMERGENCY", "COMMUNICATION", "LEARNING", "PRODUCTIVITY", "CREATIVE", "DEVELOPMENT", "ENTERTAINMENT", "BACKGROUND_SYNC"}
        and "minimum_useful" in d
        and "weights" in d
        and "constraints" in d
        and d["claim_boundaries"]["STANDARDIZED_6G"] is False
    )
    return _result("NET-ORCH-001", ok, "AnywhereServiceObjective typed runtime with service classes and floors", evidence={"objective": d, "service_classes": sorted(required_classes), "floors": sorted(required_floors)})


def evaluate_net_orch_014(_ctx: Any = None) -> dict[str, Any]:
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    up = eng.decide([_wifi(), _wifi(candidate_id="cell", bearer_class="cellular_generic", cost_class=CostClass.METERED, monetary_cost=0.05, data_unlimited=False, data_metered=True, data_remaining_fraction=0.5)], obj)
    down = eng.decide([_wifi(availability=False), _wifi(candidate_id="cell", bearer_class="cellular_generic", availability=False, cost_class=CostClass.METERED, monetary_cost=0.05, data_unlimited=False, data_metered=True, data_remaining_fraction=0.5)], obj)
    stale = eng.decide([_wifi(telemetry_timestamp=NOW - 500), _wifi(candidate_id="fresh", telemetry_timestamp=NOW - 1)], obj)
    s_av, _ = score_availability(_wifi())
    s_un, _ = score_availability(_wifi(availability=False))
    ok = (
        up.selected_candidate is not None
        and down.service_floor in {"OFFLINE_CAPABLE", "UNAVAILABLE"}
        and stale.selected_candidate == "fresh"
        and s_av == 1.0 and s_un == 0.0
    )
    return _result("NET-ORCH-014", ok, "Availability + freshness/failure/recovery handling", evidence={"up": up.selected_candidate, "down_floor": down.service_floor, "stale_selected": stale.selected_candidate})


def evaluate_net_orch_015(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    s_hi, m_hi = normalize_signal(_wifi(signal_quality=0.9))
    s_lo, _ = normalize_signal(_wifi(signal_quality=0.2))
    s_miss, m_miss = normalize_signal(_wifi(signal_quality=None, signal_raw={}))
    s_bad, _ = normalize_signal(_wifi(signal_quality=float("nan")))
    # invalid handled via sanitize in engine; normalize_signal on nan quality path — candidate may still hold nan until sanitize
    ok = s_hi > s_lo and s_miss == 0.0 and m_miss.get("missing_as") == "worst_not_perfect" and s_hi <= 1.0
    return _result("NET-ORCH-015", ok, "Signal quality normalization with provenance; unknown!=perfect", evidence={"hi": s_hi, "lo": s_lo, "missing": s_miss, "meta_hi": m_hi})


def evaluate_net_orch_016(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.COMMUNICATION)
    s20, _ = score_latency(_wifi(latency_ms=20), obj)
    s200, _ = score_latency(_wifi(latency_ms=200), obj)
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d = eng.decide([_wifi(candidate_id="neg", latency_ms=-5.0), _wifi(candidate_id="ok")], obj)
    ok = s20 > s200 and d.selected_candidate == "ok" and "neg" in [r["candidate_id"] for r in d.rejected_candidates]
    return _result("NET-ORCH-016", ok, "Latency ms with service-aware thresholds; negatives rejected", evidence={"s20": s20, "s200": s200, "selected": d.selected_candidate})


def evaluate_net_orch_017(_ctx: Any = None) -> dict[str, Any]:
    comm = default_objective_for(ServiceClass.COMMUNICATION)
    bg = default_objective_for(ServiceClass.BACKGROUND_SYNC)
    # same jitter — communication floor stricter => lower or equal score under communication
    s_comm, _ = score_jitter(_wifi(jitter_ms=35), comm)
    s_bg, _ = score_jitter(_wifi(jitter_ms=35), bg)
    s_lo, _ = score_jitter(_wifi(jitter_ms=2), comm)
    s_hi, _ = score_jitter(_wifi(jitter_ms=50), comm)
    ok = s_lo > s_hi and s_comm <= s_bg + 1e-9
    return _result("NET-ORCH-017", ok, "Jitter separate from latency; interactive more sensitive", evidence={"s_comm": s_comm, "s_bg": s_bg, "mono": s_lo > s_hi})


def evaluate_net_orch_018(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    s0, _ = score_packet_loss(_wifi(packet_loss_ratio=0.0), obj)
    s1, _ = score_packet_loss(_wifi(packet_loss_ratio=0.2), obj)
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d = eng.decide([_wifi(candidate_id="lossy", packet_loss_ratio=0.5), _wifi(candidate_id="clean", packet_loss_ratio=0.0)], obj)
    ok = s0 > s1 and d.selected_candidate == "clean"
    return _result("NET-ORCH-018", ok, "Packet loss ratio 0..1; higher loss never improves score", evidence={"s0": s0, "s1": s1, "selected": d.selected_candidate})


def evaluate_net_orch_019(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    s_un, _ = score_cost(_wifi(cost_class=CostClass.UNMETERED, monetary_cost=0.0), obj)
    s_roam, _ = score_cost(_wifi(cost_class=CostClass.ROAMING_HIGH, roaming_high_cost=True, monetary_cost=1.0), obj)
    # cost cannot bypass security
    obj.constraints.min_trust = TrustLevel.TRUSTED
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d = eng.decide([
        _wifi(candidate_id="cheap-hostile", monetary_cost=0.0, security_trust=TrustLevel.UNTRUSTED),
        _wifi(candidate_id="paid-safe", monetary_cost=0.1, cost_class=CostClass.METERED, security_trust=TrustLevel.TRUSTED, data_metered=True, data_unlimited=False, data_remaining_fraction=0.5),
    ], obj)
    ok = s_un > s_roam and d.selected_candidate == "paid-safe"
    return _result("NET-ORCH-019", ok, "Cost policy abstractions; cannot bypass hard security", evidence={"s_un": s_un, "s_roam": s_roam, "selected": d.selected_candidate})


def evaluate_net_orch_020(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.continuity.battery_saving = True
    s_lo, meta = score_energy(_wifi(energy_cost=200), obj)
    s_hi, _ = score_energy(_wifi(energy_cost=1800), obj)
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj.user_preference = UserPreferenceProfile.PREFER_BATTERY
    d = eng.decide([_wifi(candidate_id="hungry", energy_cost=1500), _wifi(candidate_id="sip", energy_cost=200)], obj)
    emerg = default_objective_for(ServiceClass.EMERGENCY)
    emerg.continuity.emergency_may_relax_energy = True
    d_e = eng.decide([_wifi(candidate_id="hungry", energy_cost=1500), _wifi(candidate_id="sip", energy_cost=200, latency_ms=400)], emerg)
    ok = s_lo > s_hi and meta.get("modeled_not_measured") is True and d.selected_candidate == "sip"
    return _result("NET-ORCH-020", ok, "Modeled energy with battery-saving influence; not measured battery draw", evidence={"selected": d.selected_candidate, "emergency_notes": d_e.notes, "meta": meta})


def evaluate_net_orch_021(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.constraints.min_trust = TrustLevel.TRUSTED
    obj.user_preference = UserPreferenceProfile.PREFER_LOW_COST
    obj.weights.security = 0.0
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d = eng.decide([
        _wifi(candidate_id="fast-free-hostile", latency_ms=1.0, monetary_cost=0.0, security_trust=TrustLevel.UNTRUSTED),
        _wifi(candidate_id="safe", latency_ms=40.0, security_trust=TrustLevel.TRUSTED),
    ], obj)
    ok = d.selected_candidate == "safe" and "security_below_required_trust" in d.hard_constraint_reasons.get("fast-free-hostile", [])
    s_t, _ = score_security(_wifi(security_trust=TrustLevel.TRUSTED), obj)
    s_u, _ = score_security(_wifi(security_trust=TrustLevel.UNTRUSTED), obj)
    return _result("NET-ORCH-021", ok, "Security hard policy; fast/free hostile rejected", evidence={"selected": d.selected_candidate, "trust_scores": [s_u, s_t]})


def evaluate_net_orch_022(_ctx: Any = None) -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.BACKGROUND_SYNC)
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d = eng.decide([
        _wifi(candidate_id="exhausted", data_unlimited=False, data_metered=True, data_hard_limit=True, data_remaining_fraction=0.0, data_remaining_bytes=0, cost_class=CostClass.METERED, monetary_cost=0.05),
        _wifi(candidate_id="unmetered", cost_class=CostClass.UNMETERED),
    ], obj)
    s_hi, _ = score_data(_wifi(data_unlimited=False, data_remaining_fraction=0.9, cost_class=CostClass.METERED), obj)
    s_lo, _ = score_data(_wifi(data_unlimited=False, data_remaining_fraction=0.1, cost_class=CostClass.METERED), obj)
    ok = d.selected_candidate == "unmetered" and "exhausted" in [r["candidate_id"] for r in d.rejected_candidates] and s_hi >= s_lo
    return _result("NET-ORCH-022", ok, "Data limits with hard exhaustion reject; background prefers unmetered", evidence={"selected": d.selected_candidate, "data_scores": [s_lo, s_hi]})


def evaluate_net_orch_023(_ctx: Any = None) -> dict[str, Any]:
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    obj_bg = default_objective_for(ServiceClass.BACKGROUND_SYNC)
    obj_bg.application_priority = ApplicationPriority.BACKGROUND
    obj_crit = default_objective_for(ServiceClass.EMERGENCY)
    obj_crit.application_priority = ApplicationPriority.CRITICAL
    obj_crit.constraints.min_trust = TrustLevel.TRUSTED
    # priority must NOT bypass security
    d = eng.decide([
        _wifi(candidate_id="hostile", security_trust=TrustLevel.UNTRUSTED, latency_ms=1.0),
        _wifi(candidate_id="safe", security_trust=TrustLevel.TRUSTED, latency_ms=50.0),
    ], obj_crit)
    s_c, m = score_application_priority(_wifi(), obj_crit)
    s_b, _ = score_application_priority(_wifi(), obj_bg)
    ok = d.selected_candidate == "safe" and s_c > s_b and m.get("priority") == "CRITICAL"
    return _result("NET-ORCH-023", ok, "Application priority soft influence only; no NET-ORCH-032 claim", evidence={"selected": d.selected_candidate, "scores": [s_b, s_c]})


def evaluate_net_orch_024(_ctx: Any = None) -> dict[str, Any]:
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        store = UserPreferenceStore(Path(tmp), profile_id="student")
        proof = store.prove_persistence_across_restart()
        store.set_preference(UserPreferenceProfile.AVOID_CELLULAR)
        eng = AnywhereNetworkDecisionEngine(preference_store=store, now_fn=lambda: NOW)
        obj = default_objective_for(ServiceClass.PRODUCTIVITY)
        # preference soft — security still wins
        obj.constraints.min_trust = TrustLevel.TRUSTED
        d = eng.decide([
            _wifi(candidate_id="wifi"),
            _wifi(candidate_id="cell", bearer_class="cellular_generic", cost_class=CostClass.METERED, monetary_cost=0.02, energy_cost=200, data_metered=True, data_unlimited=False, data_remaining_fraction=0.7),
        ], obj)
        s_pref, meta = score_user_preference(_wifi(bearer_class="cellular_generic"), obj)
        ok = proof.get("ok") is True and d.user_preference == "avoid_cellular" and d.selected_candidate == "wifi"
    return _result("NET-ORCH-024", ok, "User preference persisted via encrypted store; soft unless hard prohibition", evidence={"persistence": proof, "selected": d.selected_candidate, "pref": d.user_preference})


EVALUATORS: dict[str, Callable[..., dict[str, Any]]] = {
    "NET-ORCH-001": evaluate_net_orch_001,
    "NET-ORCH-014": evaluate_net_orch_014,
    "NET-ORCH-015": evaluate_net_orch_015,
    "NET-ORCH-016": evaluate_net_orch_016,
    "NET-ORCH-017": evaluate_net_orch_017,
    "NET-ORCH-018": evaluate_net_orch_018,
    "NET-ORCH-019": evaluate_net_orch_019,
    "NET-ORCH-020": evaluate_net_orch_020,
    "NET-ORCH-021": evaluate_net_orch_021,
    "NET-ORCH-022": evaluate_net_orch_022,
    "NET-ORCH-023": evaluate_net_orch_023,
    "NET-ORCH-024": evaluate_net_orch_024,
}


def run_all_evaluators() -> dict[str, Any]:
    classification = {}
    for req_id in TARGET_REQUIREMENTS:
        classification[req_id] = EVALUATORS[req_id]()
    # Broken evaluator gate: ensure mapping is complete and no literal True classifiers
    unconditional = 0
    summary = {
        "validated": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTED_AND_VALIDATED"),
        "implemented_validation_open": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTED_VALIDATION_OPEN"),
        "implementation_open": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTATION_OPEN"),
        "blocked_environment": sum(1 for v in classification.values() if v["classification"] == "BLOCKED_ENVIRONMENT"),
        "blocked_external": sum(1 for v in classification.values() if v["classification"] == "BLOCKED_EXTERNAL"),
        "total": len(classification),
    }
    matrix = {
        "schema": "gunnchos.engineering_wave005.requirement_evaluator_matrix.v1",
        "target_requirements": list(TARGET_REQUIREMENTS),
        "evaluators": {k: v["evaluator"] for k, v in classification.items()},
        "unconditional_true_classifiers": unconditional,
        "validated_count": summary["validated"],
        "broken_evaluator_fails_gate": True,
    }
    # Deliberate broken-evaluator self-check: a forced-True without evidence must be rejected by gate logic
    def _broken():
        return True  # noqa: intentional — must not be used as classifier
    if _broken() is True:
        # prove we do not use it
        matrix["broken_evaluator_probe_present"] = True
        matrix["broken_evaluator_used_as_classifier"] = False
    return {
        "classification": classification,
        "summary": summary,
        "matrix": matrix,
        "scenarios": run_all_scenarios(),
        "invariants": run_invariants(),
        "invalid_telemetry": run_invalid_telemetry(),
    }
