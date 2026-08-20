"""Bounded sensitivity analysis — no universal optimality claims."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.models import (
    CostClass,
    ServiceClass,
    TrustLevel,
    default_objective_for,
)

NOW = 1_700_000_000.0


def _cands() -> list[CandidatePath]:
    return [
        CandidatePath(
            candidate_id="wifi",
            bearer_class="wifi",
            availability=True,
            signal_quality=0.8,
            latency_ms=25.0,
            jitter_ms=5.0,
            packet_loss_ratio=0.01,
            monetary_cost=0.0,
            cost_class=CostClass.UNMETERED,
            energy_cost=500.0,
            security_trust=TrustLevel.TRUSTED,
            data_unlimited=True,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.95,
        ),
        CandidatePath(
            candidate_id="cell",
            bearer_class="cellular_generic",
            availability=True,
            signal_quality=0.75,
            latency_ms=40.0,
            jitter_ms=10.0,
            packet_loss_ratio=0.015,
            monetary_cost=0.08,
            cost_class=CostClass.METERED,
            energy_cost=700.0,
            security_trust=TrustLevel.TRUSTED,
            data_metered=True,
            data_remaining_fraction=0.55,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.9,
        ),
    ]


def run_sensitivity() -> dict[str, Any]:
    base_obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    base = eng.decide(_cands(), deepcopy(base_obj))
    variants = []
    sweeps = [
        ("latency_weight", {"latency": 2.5}),
        ("energy_weight", {"energy": 2.5}),
        ("cost_weight", {"cost": 2.5}),
        ("security_minimum_managed", {"min_trust": TrustLevel.MANAGED}),
        ("data_preference_unmetered_weight", {"data": 2.5, "cost": 2.0}),
    ]
    for name, patch in sweeps:
        obj = deepcopy(base_obj)
        if "min_trust" in patch:
            obj.constraints.min_trust = patch["min_trust"]
        else:
            for k, v in patch.items():
                setattr(obj.weights, k, v)
        d = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(_cands(), obj)
        variants.append({
            "variant": name,
            "selected": d.selected_candidate,
            "changed_from_base": d.selected_candidate != base.selected_candidate,
            "score_margin": None if d.selected_candidate is None else (
                d.final_scores.get(d.selected_candidate, 0) - max(
                    (v for k, v in d.final_scores.items() if k != d.selected_candidate and v != float("-inf")),
                    default=0.0,
                )
            ),
        })
    stable = sum(1 for v in variants if not v["changed_from_base"])
    return {
        "schema": "gunnchos.engineering_wave005.sensitivity.v1",
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
        "base_selected": base.selected_candidate,
        "variants": variants,
        "stable_decisions": stable,
        "boundary_changes": [v["variant"] for v in variants if v["changed_from_base"]],
        "universal_optimality_claimed": False,
        "ok": True,
    }
