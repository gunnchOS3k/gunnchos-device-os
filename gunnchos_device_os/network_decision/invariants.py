"""Property / invariant checks for the decision engine."""
from __future__ import annotations

import math
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.metrics import (
    score_energy,
    score_jitter,
    score_latency,
    score_packet_loss,
    score_data,
)
from gunnchos_device_os.network_decision.models import (
    AnywhereServiceObjective,
    CostClass,
    ServiceClass,
    TrustLevel,
    default_objective_for,
)

NOW = 1_700_000_000.0


def _cand(**kw: Any) -> CandidatePath:
    base = dict(
        candidate_id="c1",
        bearer_class="wifi",
        availability=True,
        signal_quality=0.8,
        latency_ms=30.0,
        jitter_ms=5.0,
        packet_loss_ratio=0.01,
        monetary_cost=0.0,
        cost_class=CostClass.UNMETERED,
        energy_cost=400.0,
        security_trust=TrustLevel.TRUSTED,
        data_unlimited=True,
        application_compatibility=True,
        telemetry_timestamp=NOW - 1.0,
        telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
        confidence=1.0,
    )
    base.update(kw)
    return CandidatePath(**base)


def run_invariants() -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    checks: list[dict[str, Any]] = []

    # availability=false cannot be selected
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d = eng.decide([
        _cand(candidate_id="down", availability=False),
        _cand(candidate_id="up", bearer_class="cellular_generic", cost_class=CostClass.METERED, monetary_cost=0.05, data_unlimited=False, data_metered=True, data_remaining_fraction=0.5),
    ], obj)
    checks.append({"name": "availability_false_not_selected", "ok": d.selected_candidate != "down"})

    # hard-security failure cannot be overridden by weight
    obj2 = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj2.constraints.min_trust = TrustLevel.TRUSTED
    obj2.weights.security = 0.0
    obj2.weights.latency = 5.0
    obj2.weights.cost = 5.0
    hostile = _cand(candidate_id="fast-free-hostile", latency_ms=1.0, monetary_cost=0.0, security_trust=TrustLevel.UNTRUSTED)
    safe = _cand(candidate_id="safe-slower", latency_ms=80.0, security_trust=TrustLevel.TRUSTED)
    d2 = eng.decide([hostile, safe], obj2)
    checks.append({
        "name": "hard_security_not_overridden_by_weight",
        "ok": d2.selected_candidate == "safe-slower" and "security_below_required_trust" in d2.hard_constraint_reasons.get("fast-free-hostile", []),
    })

    # higher latency alone cannot improve latency score
    c_lo = _cand(latency_ms=20.0)
    c_hi = _cand(latency_ms=100.0)
    s_lo, _ = score_latency(c_lo, obj)
    s_hi, _ = score_latency(c_hi, obj)
    checks.append({"name": "latency_monotone", "ok": s_hi <= s_lo})

    s_j_lo, _ = score_jitter(_cand(jitter_ms=2.0), obj)
    s_j_hi, _ = score_jitter(_cand(jitter_ms=40.0), obj)
    checks.append({"name": "jitter_monotone", "ok": s_j_hi <= s_j_lo})

    s_p_lo, _ = score_packet_loss(_cand(packet_loss_ratio=0.0), obj)
    s_p_hi, _ = score_packet_loss(_cand(packet_loss_ratio=0.2), obj)
    checks.append({"name": "loss_monotone", "ok": s_p_hi <= s_p_lo})

    s_d_hi, _ = score_data(_cand(data_unlimited=False, data_remaining_fraction=0.9, cost_class=CostClass.METERED), obj)
    s_d_lo, _ = score_data(_cand(data_unlimited=False, data_remaining_fraction=0.1, cost_class=CostClass.METERED), obj)
    checks.append({"name": "data_remaining_monotone", "ok": s_d_lo <= s_d_hi})

    s_e_lo, _ = score_energy(_cand(energy_cost=200.0), obj)
    s_e_hi, _ = score_energy(_cand(energy_cost=1500.0), obj)
    checks.append({"name": "energy_monotone", "ok": s_e_hi <= s_e_lo})

    # same inputs => same decision
    cands = [_cand(candidate_id="w"), _cand(candidate_id="c", bearer_class="cellular_generic", cost_class=CostClass.METERED, monetary_cost=0.05, data_unlimited=False, data_metered=True, data_remaining_fraction=0.4)]
    d_a = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(cands, obj)
    d_b = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(list(reversed(cands)), obj)
    checks.append({"name": "determinism", "ok": d_a.selected_candidate == d_b.selected_candidate and d_a.final_scores == d_b.final_scores})

    # all scores finite
    finite = True
    for scores in d_a.normalized_metric_scores.values():
        for v in scores.values():
            if not math.isfinite(v):
                finite = False
    for v in d_a.final_scores.values():
        if v != v:  # nan
            finite = False
    checks.append({"name": "scores_finite", "ok": finite})

    return {
        "schema": "gunnchos.engineering_wave005.property_invariants.v1",
        "ok": all(c["ok"] for c in checks),
        "passed": sum(1 for c in checks if c["ok"]),
        "total": len(checks),
        "checks": checks,
    }
