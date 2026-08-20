"""Metric evaluators with units, directionality, normalization, missing-value behavior."""
from __future__ import annotations

import math
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath
from gunnchos_device_os.network_decision.models import (
    AnywhereServiceObjective,
    ApplicationPriority,
    CostClass,
    ServiceClass,
    TRUST_RANK,
    TrustLevel,
    UserPreferenceProfile,
)


def _clamp01(x: float) -> float:
    if not math.isfinite(x):
        return 0.0
    return max(0.0, min(1.0, x))


def normalize_signal(candidate: CandidatePath) -> tuple[float, dict[str, Any]]:
    """Higher better. Unknown != perfect (returns 0.0 with penalty flag)."""
    meta: dict[str, Any] = {"units": "normalized_0_1", "direction": "higher_better"}
    if candidate.signal_quality is not None:
        meta["source"] = "signal_quality"
        return _clamp01(candidate.signal_quality), meta
    raw = candidate.signal_raw or {}
    if "rssi_dbm" in raw and isinstance(raw["rssi_dbm"], (int, float)) and math.isfinite(raw["rssi_dbm"]):
        # map -90..-30 -> 0..1
        v = (float(raw["rssi_dbm"]) + 90.0) / 60.0
        meta["source"] = "rssi_dbm"
        meta["provenance"] = candidate.telemetry_source.value
        return _clamp01(v), meta
    if "rsrp_dbm" in raw and isinstance(raw["rsrp_dbm"], (int, float)) and math.isfinite(raw["rsrp_dbm"]):
        v = (float(raw["rsrp_dbm"]) + 120.0) / 70.0
        meta["source"] = "rsrp_dbm"
        return _clamp01(v), meta
    if "sinr_db" in raw and isinstance(raw["sinr_db"], (int, float)) and math.isfinite(raw["sinr_db"]):
        v = (float(raw["sinr_db"]) + 5.0) / 30.0
        meta["source"] = "sinr_db"
        return _clamp01(v), meta
    meta["source"] = "missing"
    meta["missing_as"] = "worst_not_perfect"
    return 0.0, meta


def score_availability(c: CandidatePath) -> tuple[float, dict[str, Any]]:
    meta = {"units": "boolean", "direction": "true_required"}
    if c.availability is None:
        meta["missing_as"] = "unavailable"
        return 0.0, meta
    return (1.0 if c.availability else 0.0), meta


def score_latency(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    """Lower latency better. Negative rejected upstream. Unknown -> 0."""
    meta = {"units": "ms", "direction": "lower_better", "ideal": obj.ideal_latency_ms, "floor": obj.minimum_useful.max_latency_ms}
    if c.latency_ms is None:
        meta["missing_as"] = "worst"
        return 0.0, meta
    lat = c.latency_ms
    # piecewise: ideal -> 1.0; floor -> 0.2; beyond floor -> 0
    ideal = max(1.0, obj.ideal_latency_ms)
    floor = max(ideal, obj.minimum_useful.max_latency_ms)
    if lat <= ideal:
        s = 1.0
    elif lat >= floor:
        s = 0.0 if lat > floor * 1.5 else 0.2 * (1.0 - (lat - floor) / (floor * 0.5 + 1e-9))
        s = max(0.0, s)
    else:
        s = 1.0 - 0.8 * ((lat - ideal) / (floor - ideal))
    # interactive communication more sensitive already via objective weights/floors
    return _clamp01(s), meta


def score_jitter(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    meta = {"units": "ms", "direction": "lower_better", "ideal": obj.ideal_jitter_ms, "floor": obj.minimum_useful.max_jitter_ms}
    if c.jitter_ms is None:
        meta["missing_as"] = "worst"
        return 0.0, meta
    jit = c.jitter_ms
    ideal = max(0.5, obj.ideal_jitter_ms)
    floor = max(ideal, obj.minimum_useful.max_jitter_ms)
    if obj.service_class == ServiceClass.COMMUNICATION:
        # stricter mapping for interactive
        floor = min(floor, max(ideal, obj.minimum_useful.max_jitter_ms * 0.85))
    if jit <= ideal:
        s = 1.0
    elif jit >= floor:
        s = 0.0
    else:
        s = 1.0 - ((jit - ideal) / (floor - ideal))
    return _clamp01(s), meta


def score_packet_loss(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    meta = {"units": "ratio_0_1", "direction": "lower_better", "ideal": obj.ideal_packet_loss, "floor": obj.minimum_useful.max_packet_loss}
    if c.packet_loss_ratio is None:
        meta["missing_as"] = "worst"
        return 0.0, meta
    loss = c.packet_loss_ratio
    # higher loss must never improve score: monotone decreasing
    ideal = max(0.0, obj.ideal_packet_loss)
    floor = max(ideal + 1e-9, obj.minimum_useful.max_packet_loss)
    if loss <= ideal:
        s = 1.0
    elif loss >= floor:
        s = 0.0
    else:
        s = 1.0 - ((loss - ideal) / (floor - ideal))
    return _clamp01(s), meta


def score_cost(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    meta = {"units": "policy_abstract", "direction": "lower_cost_better"}
    if c.cost_class == CostClass.UNKNOWN and c.monetary_cost is None:
        meta["missing_as"] = "neutral_low_not_best"
        return 0.35, meta
    if c.cost_class == CostClass.UNMETERED or (c.monetary_cost is not None and c.monetary_cost <= 0 and not c.roaming_high_cost):
        return 1.0, meta | {"cost_class": c.cost_class.value}
    if c.cost_class == CostClass.ROAMING_HIGH or c.roaming_high_cost:
        return 0.1, meta | {"cost_class": "roaming_high_cost"}
    if c.monetary_cost is None:
        # metered unknown magnitude
        return 0.45, meta | {"cost_class": c.cost_class.value}
    # relative cost 0..2 mapped
    return _clamp01(1.0 - min(1.0, float(c.monetary_cost))), meta


def score_energy(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    meta = {"units": "modeled_mw_equiv", "direction": "lower_better", "modeled_not_measured": True}
    if c.energy_cost is None:
        meta["missing_as"] = "neutral_low_not_best"
        return 0.35, meta
    # map 0..2000 mW -> 1..0
    s = 1.0 - min(1.0, float(c.energy_cost) / 2000.0)
    if obj.continuity.battery_saving:
        # emphasize energy via caller weight; score itself unchanged monotone
        meta["battery_saving"] = True
    if obj.service_class == ServiceClass.EMERGENCY and obj.continuity.emergency_may_relax_energy:
        meta["energy_relaxed_for_emergency"] = True
    return _clamp01(s), meta


def score_security(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    meta = {"units": "trust_level", "direction": "higher_better"}
    rank = TRUST_RANK.get(c.security_trust, 0)
    return _clamp01(rank / 3.0), meta | {"trust": c.security_trust.value}


def score_data(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    meta = {"units": "quota_abstract", "direction": "more_remaining_better"}
    if c.data_unlimited or c.cost_class == CostClass.UNMETERED:
        return 1.0, meta | {"state": "unlimited_or_unmetered"}
    if c.data_remaining_fraction is not None and math.isfinite(c.data_remaining_fraction):
        frac = _clamp01(float(c.data_remaining_fraction))
        # lower remaining cannot improve score
        return frac, meta | {"state": "remaining_fraction"}
    if c.data_remaining_bytes is not None:
        # unknown cap -> soft map using log-ish; treat 0 as worst
        if c.data_remaining_bytes <= 0:
            return 0.0, meta | {"state": "exhausted"}
        return 0.5, meta | {"state": "remaining_bytes_unknown_cap"}
    if c.data_metered or c.cost_class == CostClass.METERED:
        return 0.4, meta | {"state": "metered_unknown_remaining"}
    return 0.35, meta | {"state": "unknown"}


def score_application_priority(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    """Priority is an input affecting willingness — compatibility gate already hard."""
    meta = {"units": "priority_class", "direction": "context"}
    p = obj.application_priority
    base = {
        ApplicationPriority.CRITICAL: 1.0,
        ApplicationPriority.HIGH: 0.85,
        ApplicationPriority.NORMAL: 0.7,
        ApplicationPriority.LOW: 0.5,
        ApplicationPriority.BACKGROUND: 0.35,
    }[p]
    if not c.application_compatibility:
        return 0.0, meta | {"compatible": False}
    return base, meta | {"compatible": True, "priority": p.value}


def score_user_preference(c: CandidatePath, obj: AnywhereServiceObjective) -> tuple[float, dict[str, Any]]:
    pref = obj.user_preference
    meta = {"units": "preference_match_0_1", "direction": "higher_better", "preference": pref.value}
    b = c.normalized_bearer()
    s = 0.5
    if pref == UserPreferenceProfile.BALANCED:
        s = 0.6
    elif pref == UserPreferenceProfile.PREFER_PERFORMANCE:
        s = 0.9 if b in {"ethernet", "wifi"} else (0.55 if b == "cellular_generic" else 0.3)
        if c.latency_ms is not None and c.latency_ms < 40:
            s = min(1.0, s + 0.1)
    elif pref == UserPreferenceProfile.PREFER_LOW_COST:
        s = 0.95 if c.cost_class == CostClass.UNMETERED or (c.monetary_cost is not None and c.monetary_cost <= 0) else 0.25
    elif pref == UserPreferenceProfile.PREFER_BATTERY:
        if c.energy_cost is None:
            s = 0.4
        else:
            s = _clamp01(1.0 - min(1.0, c.energy_cost / 1500.0))
    elif pref == UserPreferenceProfile.PREFER_UNMETERED:
        s = 1.0 if c.cost_class == CostClass.UNMETERED else 0.2
    elif pref == UserPreferenceProfile.PREFER_TRUSTED:
        s = TRUST_RANK.get(c.security_trust, 0) / 3.0
    elif pref == UserPreferenceProfile.AVOID_CELLULAR:
        s = 0.1 if b == "cellular_generic" else 0.8
    elif pref == UserPreferenceProfile.AVOID_METERED:
        s = 0.1 if (c.data_metered or c.cost_class in {CostClass.METERED, CostClass.ROAMING_HIGH}) else 0.85
    return _clamp01(s), meta


def score_uncertainty(c: CandidatePath, obj: AnywhereServiceObjective, *, now_ts: float, invalid_flags: list[str]) -> tuple[float, dict[str, Any]]:
    """Penalty term: returns remaining confidence mass (higher better)."""
    meta = {"units": "confidence_0_1", "direction": "higher_better"}
    conf = 1.0
    if c.confidence is not None:
        conf = min(conf, _clamp01(c.confidence))
    if c.telemetry_timestamp is None:
        conf *= 0.7
        meta["missing_timestamp"] = True
    else:
        age = now_ts - c.telemetry_timestamp
        meta["telemetry_age_s"] = age
        max_age = obj.continuity.max_telemetry_age_s
        if age > max_age:
            conf *= 0.2
            meta["stale"] = True
        elif age > max_age * 0.5:
            conf *= 0.7
    if invalid_flags:
        conf *= max(0.1, 1.0 - 0.15 * len(invalid_flags))
        meta["invalid_flags"] = list(invalid_flags)
    if c.telemetry_source.value == "UNKNOWN":
        conf *= 0.85
    return _clamp01(conf), meta


def evaluate_all_metrics(
    c: CandidatePath,
    obj: AnywhereServiceObjective,
    *,
    now_ts: float,
    invalid_flags: list[str],
) -> dict[str, Any]:
    parts = {
        "availability": score_availability(c),
        "signal": normalize_signal(c),
        "latency": score_latency(c, obj),
        "jitter": score_jitter(c, obj),
        "packet_loss": score_packet_loss(c, obj),
        "cost": score_cost(c, obj),
        "energy": score_energy(c, obj),
        "security": score_security(c, obj),
        "data": score_data(c, obj),
        "application_priority": score_application_priority(c, obj),
        "user_preference": score_user_preference(c, obj),
        "uncertainty": score_uncertainty(c, obj, now_ts=now_ts, invalid_flags=invalid_flags),
    }
    scores = {k: float(v[0]) for k, v in parts.items()}
    meta = {k: v[1] for k, v in parts.items()}
    for k, s in scores.items():
        if not math.isfinite(s):
            scores[k] = 0.0
            meta[k] = {**meta[k], "non_finite_replaced": True}
    return {"scores": scores, "meta": meta}
