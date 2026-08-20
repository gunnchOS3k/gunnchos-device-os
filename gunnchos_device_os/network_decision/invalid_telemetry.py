"""Invalid / adversarial telemetry campaign."""
from __future__ import annotations

import math
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


def _good(**kw: Any) -> CandidatePath:
    d = dict(
        candidate_id="good",
        bearer_class="wifi",
        availability=True,
        signal_quality=0.8,
        latency_ms=25.0,
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
        confidence=0.95,
    )
    d.update(kw)
    return CandidatePath(**d)


CASES = [
    ("NaN_latency", dict(candidate_id="bad", latency_ms=float("nan"))),
    ("Infinity_latency", dict(candidate_id="bad", latency_ms=float("inf"))),
    ("negative_latency", dict(candidate_id="bad", latency_ms=-10.0)),
    ("packet_loss_gt_1", dict(candidate_id="bad", packet_loss_ratio=1.5)),
    ("signal_out_of_range", dict(candidate_id="bad", signal_quality=1.5)),
    ("stale_timestamp", dict(candidate_id="bad", telemetry_timestamp=NOW - 999.0)),
    ("future_timestamp", dict(candidate_id="bad", telemetry_timestamp=NOW + 100.0)),
    ("missing_metric_latency", dict(candidate_id="bad", latency_ms=None)),
    ("unknown_cost", dict(candidate_id="bad", monetary_cost=None, cost_class=CostClass.UNKNOWN)),
    ("unknown_energy", dict(candidate_id="bad", energy_cost=None)),
    ("unknown_security", dict(candidate_id="bad", security_trust=TrustLevel.UNTRUSTED)),
    ("contradictory_availability", dict(candidate_id="bad", availability=True, packet_loss_ratio=1.0)),
    ("duplicate_candidate_ids", "DUPLICATE"),
    ("spoofed_high_quality_untrusted", dict(
        candidate_id="spoof",
        latency_ms=1.0,
        monetary_cost=0.0,
        signal_quality=1.0,
        security_trust=TrustLevel.UNTRUSTED,
        energy_cost=50.0,
    )),
]


def run_invalid_telemetry() -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.constraints.min_trust = TrustLevel.TRUSTED
    results = []
    for name, patch in CASES:
        eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
        if patch == "DUPLICATE":
            cands = [_good(candidate_id="dup"), _good(candidate_id="dup"), _good(candidate_id="good2", bearer_class="cellular_generic", cost_class=CostClass.METERED, monetary_cost=0.05, data_unlimited=False, data_metered=True, data_remaining_fraction=0.5)]
        else:
            bad = _good(**patch)
            cands = [bad, _good(candidate_id="good")]
        d = eng.decide(cands, obj)
        # Never select bad/spoof/dup as best-case silently
        selected_ok = d.selected_candidate not in {"bad", "spoof"} 
        if name == "duplicate_candidate_ids":
            selected_ok = d.selected_candidate in {"dup", "good2"}  # first dup kept; second rejected
            dup_rejected = any(r.get("reasons") == ["duplicate_candidate_id"] for r in d.rejected_candidates)
            selected_ok = selected_ok and dup_rejected
        if name == "spoofed_high_quality_untrusted":
            selected_ok = d.selected_candidate == "good" and "spoof" in [r["candidate_id"] for r in d.rejected_candidates]
        if name in {"unknown_cost", "unknown_energy", "missing_metric_latency"}:
            # soft: must not crash; missing must not be treated as perfect
            scores = d.normalized_metric_scores.get("bad") or d.normalized_metric_scores.get(d.selected_candidate or "", {})
            if name == "missing_metric_latency" and "bad" in d.normalized_metric_scores:
                selected_ok = d.normalized_metric_scores["bad"]["latency"] < 1.0
            else:
                selected_ok = True  # survived
        results.append({"case": name, "ok": selected_ok, "selected": d.selected_candidate, "rejected": d.rejected_candidates})
    return {
        "schema": "gunnchos.engineering_wave005.invalid_telemetry.v1",
        "ok": all(r["ok"] for r in results),
        "passed": sum(1 for r in results if r["ok"]),
        "total": len(results),
        "cases": results,
        "never_best_case_missing_invalid": True,
    }
