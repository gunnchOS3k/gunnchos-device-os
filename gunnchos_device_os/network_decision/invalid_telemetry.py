"""Invalid / adversarial telemetry campaign — computed never-best-case proofs."""
from __future__ import annotations

import math
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance, sanitize_candidate
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.metrics import score_cost, score_energy, score_latency
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
    ("unknown_security", dict(candidate_id="bad", extra={"security_trust_raw": "NOT_A_TRUST_LEVEL"})),
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
    ("invalid_jitter", dict(candidate_id="bad", jitter_ms=float("nan"))),
    ("negative_jitter", dict(candidate_id="bad", jitter_ms=-3.0)),
    ("invalid_cost_nan", dict(candidate_id="bad", monetary_cost=float("nan"))),
    ("invalid_cost_inf", dict(candidate_id="bad", monetary_cost=float("inf"))),
    ("invalid_energy_nan", dict(candidate_id="bad", energy_cost=float("nan"))),
    ("invalid_energy_inf", dict(candidate_id="bad", energy_cost=float("inf"))),
    ("negative_energy", dict(candidate_id="bad", energy_cost=-50.0)),
    ("invalid_confidence", dict(candidate_id="bad", confidence=float("nan"))),
    ("invalid_timestamp", dict(candidate_id="bad", telemetry_timestamp=float("nan"))),
]


def _prove_unknown_not_best() -> dict[str, Any]:
    """Prove unknown/missing metrics are not treated as best-case vs known-good twins."""
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.continuity.battery_saving = True
    proofs: dict[str, Any] = {}

    known_free = _good(candidate_id="known-free", monetary_cost=0.0, cost_class=CostClass.UNMETERED)
    unknown_cost = _good(candidate_id="unknown-cost", monetary_cost=None, cost_class=CostClass.UNKNOWN)
    s_known, m_known = score_cost(known_free, obj)
    s_unknown, m_unknown = score_cost(unknown_cost, obj)
    eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
    d_cost = eng.decide([unknown_cost, known_free], obj)
    proofs["unknown_cost"] = {
        "ok": s_unknown <= s_known and d_cost.selected_candidate == "known-free" and m_unknown.get("missing_as") is not None,
        "score_unknown": s_unknown,
        "score_known_unmetered": s_known,
        "selected": d_cost.selected_candidate,
        "meta": m_unknown,
    }

    known_low_e = _good(candidate_id="known-low-e", energy_cost=150.0)
    unknown_e = _good(candidate_id="unknown-e", energy_cost=None)
    s_ke, _ = score_energy(known_low_e, obj)
    s_ue, m_ue = score_energy(unknown_e, obj)
    d_e = eng.decide([unknown_e, known_low_e], obj)
    proofs["unknown_energy"] = {
        "ok": s_ue <= s_ke and d_e.selected_candidate == "known-low-e" and m_ue.get("missing_as") is not None,
        "score_unknown": s_ue,
        "score_known_low": s_ke,
        "selected": d_e.selected_candidate,
    }

    comm = default_objective_for(ServiceClass.COMMUNICATION)
    known_lat = _good(candidate_id="known-lat", latency_ms=20.0)
    missing_lat = _good(candidate_id="missing-lat", latency_ms=None)
    s_kl, _ = score_latency(known_lat, comm)
    s_ml, m_ml = score_latency(missing_lat, comm)
    d_lat = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide([missing_lat, known_lat], comm)
    proofs["missing_latency"] = {
        "ok": s_ml < s_kl and d_lat.selected_candidate == "known-lat",
        "score_missing": s_ml,
        "score_known": s_kl,
        "selected": d_lat.selected_candidate,
        "meta": m_ml,
    }

    # unknown security via sanitizer
    raw = _good(candidate_id="sec-unknown", extra={"security_trust_raw": "GARBAGE_TRUST"})
    sanitized, flags = sanitize_candidate(raw, now_ts=NOW)
    proofs["unknown_security"] = {
        "ok": "unknown_security" in flags and sanitized.security_trust == TrustLevel.UNTRUSTED,
        "flags": flags,
        "trust": sanitized.security_trust.value,
    }

    return {
        "ok": all(v["ok"] for v in proofs.values()),
        "proofs": proofs,
    }


def run_invalid_telemetry() -> dict[str, Any]:
    obj = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj.constraints.min_trust = TrustLevel.TRUSTED
    results = []
    never_best_flags: list[bool] = []

    for name, patch in CASES:
        eng = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW)
        if patch == "DUPLICATE":
            cands = [
                _good(candidate_id="dup"),
                _good(candidate_id="dup"),
                _good(
                    candidate_id="good2",
                    bearer_class="cellular_generic",
                    cost_class=CostClass.METERED,
                    monetary_cost=0.05,
                    data_unlimited=False,
                    data_metered=True,
                    data_remaining_fraction=0.5,
                ),
            ]
        else:
            bad = _good(**patch)
            cands = [bad, _good(candidate_id="good")]
        d = eng.decide(cands, obj)
        selected_ok = d.selected_candidate not in {"bad", "spoof"}
        case_never_best = True

        if name == "duplicate_candidate_ids":
            dup_rejected = any(r.get("reasons") == ["duplicate_candidate_id"] for r in d.rejected_candidates)
            selected_ok = d.selected_candidate in {"dup", "good2"} and dup_rejected
            case_never_best = dup_rejected
        elif name == "spoofed_high_quality_untrusted":
            selected_ok = d.selected_candidate == "good" and "spoof" in [r["candidate_id"] for r in d.rejected_candidates]
            case_never_best = selected_ok
        elif name == "unknown_cost":
            s_bad = d.normalized_metric_scores.get("bad", {}).get("cost", 1.0)
            s_good = d.normalized_metric_scores.get("good", {}).get("cost", 0.0)
            selected_ok = s_bad <= s_good and d.selected_candidate != "bad"
            case_never_best = selected_ok
        elif name == "unknown_energy":
            s_bad = d.normalized_metric_scores.get("bad", {}).get("energy", 1.0)
            s_good = d.normalized_metric_scores.get("good", {}).get("energy", 0.0)
            selected_ok = s_bad <= s_good and d.selected_candidate != "bad"
            case_never_best = selected_ok
        elif name == "missing_metric_latency":
            s_bad = d.normalized_metric_scores.get("bad", {}).get("latency", 1.0)
            s_good = d.normalized_metric_scores.get("good", {}).get("latency", 0.0)
            selected_ok = s_bad < s_good and d.selected_candidate != "bad"
            case_never_best = selected_ok
        elif name == "unknown_security":
            selected_ok = (
                d.selected_candidate == "good"
                and "bad" in [r["candidate_id"] for r in d.rejected_candidates]
            )
            case_never_best = selected_ok
        else:
            # invalid/adversarial must not silently win as best
            if d.selected_candidate == "bad":
                selected_ok = False
                case_never_best = False
            else:
                case_never_best = True

        never_best_flags.append(case_never_best)
        results.append({
            "case": name,
            "ok": selected_ok,
            "never_best_case": case_never_best,
            "selected": d.selected_candidate,
            "rejected": d.rejected_candidates,
        })

    twin_proofs = _prove_unknown_not_best()
    never_best = all(never_best_flags) and twin_proofs["ok"]
    return {
        "schema": "gunnchos.engineering_wave005.invalid_telemetry.v1",
        "ok": all(r["ok"] for r in results) and twin_proofs["ok"],
        "passed": sum(1 for r in results if r["ok"]),
        "total": len(results),
        "cases": results,
        "never_best_case_missing_invalid": never_best,
        "NEVER_BEST_CASE_MISSING_INVALID": never_best,
        "NEVER_BEST_CASE_MISSING_INVALID_COMPUTED": True,
        "twin_proofs": twin_proofs,
    }
