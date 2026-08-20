"""Two-stage Anywhere Network Decision Engine wrapping ConnectivityOrchestrator."""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from gunnchos_device_os.connectivity_orchestrator import (
    BearerKind,
    BearerMetrics,
    ConnectivityOrchestrator,
    OrchestratorState,
)
from gunnchos_device_os.diagnostics_log import DiagnosticsLog, redact
from gunnchos_device_os.network_decision.candidate import CandidatePath, sanitize_candidate
from gunnchos_device_os.network_decision.metrics import evaluate_all_metrics
from gunnchos_device_os.network_decision.models import (
    CLAIM_BOUNDARIES,
    AnywhereServiceObjective,
    ApplicationPriority,
    CostClass,
    ServiceClass,
    ServiceFloor,
    TRUST_RANK,
    TrustLevel,
)
from gunnchos_device_os.network_decision.preferences import UserPreferenceStore

BEARER_TO_ORCH = {
    "ethernet": BearerKind.ETHERNET,
    "wifi": BearerKind.WIFI,
    "peer_local": BearerKind.BLUETOOTH,
    "cellular_generic": BearerKind.CELLULAR,
    "ntn_simulated": BearerKind.NTN_SIMULATED,
    "offline": BearerKind.OFFLINE,
}

# Deterministic tie-break priority (stable, not dict order)
TIE_BREAK_BEARER_ORDER = (
    "ethernet",
    "wifi",
    "cellular_generic",
    "ntn_simulated",
    "peer_local",
    "offline",
)


@dataclass
class DecisionExplanation:
    selected_candidate: str | None
    admissible_candidates: list[str]
    rejected_candidates: list[dict[str, Any]]
    hard_constraint_reasons: dict[str, list[str]]
    normalized_metric_scores: dict[str, dict[str, float]]
    weights: dict[str, float]
    penalties: dict[str, float]
    final_scores: dict[str, float]
    tie_break_reason: str | None
    service_objective: dict[str, Any]
    application_priority: str
    user_preference: str
    telemetry_sources: dict[str, str]
    telemetry_age: dict[str, float | None]
    claim_boundaries: dict[str, bool]
    service_floor: str
    orchestrator_state: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hard_reject(candidate: CandidatePath, obj: AnywhereServiceObjective, *, now_ts: float, flags: list[str]) -> list[str]:
    reasons: list[str] = []
    b = candidate.normalized_bearer()
    if candidate.admin_prohibited:
        reasons.append("explicit_admin_prohibition")
    if b in obj.constraints.hard_prohibit_bearers:
        reasons.append("bearer_hard_prohibited")
    if candidate.availability is not True and b != "offline":
        reasons.append("unavailable")
    if not candidate.application_compatibility:
        reasons.append("incompatible_service_capability")

    # security hard gate — user preference cannot weaken
    min_trust = obj.constraints.min_trust
    if TRUST_RANK.get(candidate.security_trust, 0) < TRUST_RANK.get(min_trust, 0):
        reasons.append("security_below_required_trust")
    if TRUST_RANK.get(candidate.security_trust, 0) < TRUST_RANK.get(obj.minimum_useful.min_security, 0):
        reasons.append("security_below_minimum_useful")

    # data hard limit
    exhausted = (
        (candidate.data_remaining_fraction is not None and candidate.data_remaining_fraction <= 0)
        or (candidate.data_remaining_bytes is not None and candidate.data_remaining_bytes <= 0)
        or (candidate.data_hard_limit and candidate.data_remaining_fraction is not None and candidate.data_remaining_fraction <= 0)
    )
    if exhausted:
        emergency_ok = (
            obj.service_class == ServiceClass.EMERGENCY
            and obj.constraints.allow_emergency_data_exception
            and obj.continuity.emergency_may_use_metered_hard_limit
        )
        if not emergency_ok:
            reasons.append("hard_data_limit_exhausted")

    if obj.constraints.hard_prohibit_metered and (
        candidate.data_metered or candidate.cost_class in {CostClass.METERED, CostClass.ROAMING_HIGH}
    ):
        reasons.append("metered_hard_prohibited")

    if (
        obj.constraints.require_unmetered_for_background
        and obj.application_priority == ApplicationPriority.BACKGROUND
        and candidate.cost_class != CostClass.UNMETERED
        and b != "offline"
    ):
        reasons.append("background_requires_unmetered")

    # HARD user preference policy (NET-ORCH-024) — subordinate to security/admin already checked
    pref_policy = obj.preference_policy
    if pref_policy is not None and pref_policy.enforcement_mode.value == "HARD":
        if b in pref_policy.hard_avoid_bearers and b != "offline":
            reasons.append("user_hard_avoid_bearer")
        if pref_policy.hard_avoid_metered and (
            candidate.data_metered or candidate.cost_class in {CostClass.METERED, CostClass.ROAMING_HIGH}
        ):
            # emergency/admin may still override only when explicitly allowed
            emergency_override = (
                obj.service_class == ServiceClass.EMERGENCY
                and obj.constraints.allow_emergency_data_exception
            )
            if not emergency_override:
                reasons.append("user_hard_avoid_metered")

    # telemetry invalid/stale beyond policy
    if "future_timestamp" in flags and obj.continuity.reject_future_timestamps:
        reasons.append("future_timestamp_rejected")
    if candidate.telemetry_timestamp is not None:
        age = now_ts - candidate.telemetry_timestamp
        if age > obj.continuity.max_telemetry_age_s and b != "offline":
            reasons.append("telemetry_stale_beyond_policy")
    elif b != "offline" and obj.continuity.max_telemetry_age_s < 1e9:
        # missing timestamp treated as stale for hard gate when policy is strict (<=30 default)
        if obj.continuity.max_telemetry_age_s <= 60:
            reasons.append("telemetry_timestamp_missing")

    severe_invalid = {
        "invalid_latency", "negative_latency", "packet_loss_out_of_range",
        "invalid_packet_loss", "signal_out_of_range", "invalid_signal",
        "contradictory_availability_total_loss", "unknown_bearer_class",
    }
    if severe_invalid.intersection(flags) and b != "offline":
        reasons.append("telemetry_invalid")

    # minimum useful soft thresholds can force reject for non-offline when clearly unusable
    if b != "offline" and candidate.availability is True:
        if candidate.packet_loss_ratio is not None and candidate.packet_loss_ratio > obj.minimum_useful.max_packet_loss * 2:
            reasons.append("loss_below_minimum_useful_service")
        if candidate.latency_ms is not None and candidate.latency_ms > obj.minimum_useful.max_latency_ms * 3:
            reasons.append("latency_below_minimum_useful_service")

    return reasons


def _utility(scores: dict[str, float], weights: dict[str, float]) -> float:
    total_w = 0.0
    acc = 0.0
    for k, w in weights.items():
        if k not in scores:
            continue
        ww = float(w)
        if ww <= 0:
            continue
        acc += ww * float(scores[k])
        total_w += ww
    if total_w <= 0:
        return 0.0
    u = acc / total_w
    return u if math.isfinite(u) else 0.0


def _apply_preference_weight_tilt(obj: AnywhereServiceObjective) -> dict[str, float]:
    w = asdict(obj.weights.clamped())
    pref = obj.user_preference.value
    if pref == "prefer_performance":
        w["latency"] *= 1.4
        w["jitter"] *= 1.2
    elif pref == "prefer_low_cost":
        w["cost"] *= 1.6
        w["data"] *= 1.2
    elif pref == "prefer_battery":
        w["energy"] *= 2.4
        w["user_preference"] *= 1.6
    elif pref == "prefer_unmetered":
        w["cost"] *= 1.3
        w["data"] *= 1.3
    elif pref == "prefer_trusted":
        w["security"] *= 1.5
    elif pref == "avoid_cellular":
        w["user_preference"] *= 1.4
    elif pref == "avoid_metered":
        w["cost"] *= 1.3
        w["data"] *= 1.3
    if obj.continuity.battery_saving:
        w["energy"] *= 1.5
    if obj.service_class == ServiceClass.EMERGENCY and obj.continuity.emergency_may_relax_energy:
        w["energy"] *= 0.3
        w["cost"] *= 0.3
    if obj.application_priority == ApplicationPriority.CRITICAL:
        w["latency"] *= 1.8
        w["jitter"] *= 1.4
        w["availability"] *= 1.3
        w["energy"] *= 0.35
        w["cost"] *= 0.5
    elif obj.application_priority == ApplicationPriority.HIGH:
        w["latency"] *= 1.35
        w["jitter"] *= 1.2
        w["energy"] *= 0.7
    elif obj.application_priority == ApplicationPriority.BACKGROUND:
        w["cost"] *= 1.4
        w["energy"] *= 2.2
        w["data"] *= 1.3
        w["latency"] *= 0.55
        w["jitter"] *= 0.6
    elif obj.application_priority == ApplicationPriority.LOW:
        w["energy"] *= 1.3
        w["cost"] *= 1.2
        w["latency"] *= 0.8
    return w


def _infer_floor(selected: CandidatePath | None, utility: float, obj: AnywhereServiceObjective, rejected_all_online: bool) -> ServiceFloor:
    if selected is None or selected.normalized_bearer() == "offline":
        if obj.continuity.allow_offline_fallback:
            return ServiceFloor.OFFLINE_CAPABLE
        return ServiceFloor.UNAVAILABLE
    if rejected_all_online and selected.normalized_bearer() == "offline":
        return ServiceFloor.OFFLINE_CAPABLE
    if utility >= 0.85:
        return ServiceFloor.IDEAL if obj.target_floor == ServiceFloor.IDEAL else ServiceFloor.FULL
    if utility >= 0.65:
        return ServiceFloor.FULL
    if utility >= 0.45:
        return ServiceFloor.REDUCED
    if utility >= 0.25:
        return ServiceFloor.MINIMUM_USEFUL
    return ServiceFloor.MINIMUM_USEFUL


def _tie_break_key(candidate_id: str, bearer: str) -> tuple[int, str]:
    try:
        idx = TIE_BREAK_BEARER_ORDER.index(bearer)
    except ValueError:
        idx = 99
    return (idx, candidate_id)


class AnywhereNetworkDecisionEngine:
    """Hard admissibility + explainable utility; syncs into ConnectivityOrchestrator."""

    def __init__(
        self,
        *,
        orchestrator: ConnectivityOrchestrator | None = None,
        preference_store: UserPreferenceStore | None = None,
        diagnostics: DiagnosticsLog | None = None,
        now_fn: Any = None,
    ) -> None:
        self.orchestrator = orchestrator or ConnectivityOrchestrator()
        self.preference_store = preference_store
        self.diagnostics = diagnostics
        self.now_fn = now_fn or (lambda: time.time())
        self.last_decision: DecisionExplanation | None = None

    def decide(
        self,
        candidates: list[CandidatePath],
        objective: AnywhereServiceObjective,
        *,
        apply_to_orchestrator: bool = True,
    ) -> DecisionExplanation:
        now_ts = float(self.now_fn())
        if self.preference_store is not None:
            loaded_policy = None
            get_policy = getattr(self.preference_store, "get_policy", None)
            if callable(get_policy):
                loaded_policy = get_policy()
            if loaded_policy is not None:
                objective.preference_policy = loaded_policy
                objective.user_preference = loaded_policy.preference
            else:
                loaded = self.preference_store.get_preference()
                if loaded is not None:
                    objective.user_preference = loaded

        # Priority authority resolution (NET-ORCH-023) — late import avoids cycles
        from gunnchos_device_os.network_decision.priority_authority import apply_priority_to_objective

        apply_priority_to_objective(objective)

        # duplicate IDs
        seen: set[str] = set()
        deduped: list[CandidatePath] = []
        dup_rejects: list[dict[str, Any]] = []
        for c in candidates:
            if c.candidate_id in seen:
                dup_rejects.append({"candidate_id": c.candidate_id, "reasons": ["duplicate_candidate_id"]})
                continue
            seen.add(c.candidate_id)
            deduped.append(c)

        weights = _apply_preference_weight_tilt(objective)
        hard_reasons: dict[str, list[str]] = {}
        rejected: list[dict[str, Any]] = list(dup_rejects)
        admissible: list[tuple[CandidatePath, dict[str, float], list[str], float]] = []
        metric_scores: dict[str, dict[str, float]] = {}
        penalties: dict[str, float] = {}
        telemetry_sources: dict[str, str] = {}
        telemetry_age: dict[str, float | None] = {}
        final_scores: dict[str, float] = {}

        for raw in deduped:
            c, flags = sanitize_candidate(raw, now_ts=now_ts)
            telemetry_sources[c.candidate_id] = c.telemetry_source.value
            if c.telemetry_timestamp is None:
                telemetry_age[c.candidate_id] = None
            else:
                telemetry_age[c.candidate_id] = now_ts - c.telemetry_timestamp
            reasons = _hard_reject(c, objective, now_ts=now_ts, flags=flags)
            hard_reasons[c.candidate_id] = reasons
            metrics = evaluate_all_metrics(c, objective, now_ts=now_ts, invalid_flags=flags)
            metric_scores[c.candidate_id] = metrics["scores"]
            # uncertainty already in scores; penalty = 1 - uncertainty
            penalties[c.candidate_id] = 1.0 - metrics["scores"]["uncertainty"]
            if reasons:
                rejected.append({"candidate_id": c.candidate_id, "reasons": reasons, "flags": flags})
                final_scores[c.candidate_id] = float("-inf")
                continue
            u = _utility(metrics["scores"], weights)
            # apply uncertainty as multiplicative penalty on utility
            u = u * metrics["scores"]["uncertainty"]
            if not math.isfinite(u):
                u = 0.0
            final_scores[c.candidate_id] = u
            admissible.append((c, metrics["scores"], flags, u))

        # ensure offline fallback if allowed and no online admissible
        online_adm = [a for a in admissible if a[0].normalized_bearer() != "offline"]
        if not online_adm and objective.continuity.allow_offline_fallback:
            offline_existing = [a for a in admissible if a[0].normalized_bearer() == "offline"]
            if not offline_existing:
                off = CandidatePath(
                    candidate_id="offline-fallback",
                    bearer_class="offline",
                    availability=True,
                    latency_ms=0.0,
                    jitter_ms=0.0,
                    packet_loss_ratio=0.0,
                    monetary_cost=0.0,
                    cost_class=CostClass.UNMETERED,
                    energy_cost=1.0,
                    security_trust=TrustLevel.TRUSTED,
                    data_unlimited=True,
                    application_compatibility=True,
                    telemetry_timestamp=now_ts,
                    confidence=1.0,
                )
                metrics = evaluate_all_metrics(off, objective, now_ts=now_ts, invalid_flags=[])
                metric_scores[off.candidate_id] = metrics["scores"]
                u = _utility(metrics["scores"], weights) * 0.05  # last resort
                final_scores[off.candidate_id] = u
                admissible.append((off, metrics["scores"], [], u))
                hard_reasons[off.candidate_id] = []

        selected: CandidatePath | None = None
        tie_reason: str | None = None
        if admissible:
            # sort by utility desc, then deterministic tie-break
            ranked = sorted(
                admissible,
                key=lambda item: (-item[3], _tie_break_key(item[0].candidate_id, item[0].normalized_bearer())),
            )
            best_u = ranked[0][3]
            tied = [r for r in ranked if abs(r[3] - best_u) < 1e-12]
            if len(tied) > 1:
                tied_sorted = sorted(tied, key=lambda item: _tie_break_key(item[0].candidate_id, item[0].normalized_bearer()))
                selected = tied_sorted[0][0]
                tie_reason = (
                    f"utility_tie:{best_u:.6f};bearer_order+candidate_id;"
                    f"selected={selected.candidate_id}"
                )
            else:
                selected = ranked[0][0]
                tie_reason = None

        floor = _infer_floor(
            selected,
            final_scores.get(selected.candidate_id, 0.0) if selected else 0.0,
            objective,
            rejected_all_online=not online_adm,
        )

        orch_state = None
        if apply_to_orchestrator and selected is not None:
            orch_state = self._sync_orchestrator(selected, admissible)

        notes: list[str] = []
        if objective.service_class == ServiceClass.EMERGENCY and objective.continuity.emergency_may_relax_energy:
            notes.append("energy_preference_relaxed_for_emergency")
        # insecure fast/free recording
        for r in rejected:
            if "security_below_required_trust" in r.get("reasons", []):
                notes.append(f"rejected_insecure:{r['candidate_id']}")

        explanation = DecisionExplanation(
            selected_candidate=selected.candidate_id if selected else None,
            admissible_candidates=[a[0].candidate_id for a in admissible],
            rejected_candidates=rejected,
            hard_constraint_reasons=hard_reasons,
            normalized_metric_scores=metric_scores,
            weights=weights,
            penalties=penalties,
            final_scores={k: (v if math.isfinite(v) else -1e300) for k, v in final_scores.items()},
            tie_break_reason=tie_reason,
            service_objective=objective.to_dict(),
            application_priority=objective.application_priority.value,
            user_preference=objective.user_preference.value,
            telemetry_sources=telemetry_sources,
            telemetry_age=telemetry_age,
            claim_boundaries=dict(CLAIM_BOUNDARIES),
            service_floor=floor.value,
            orchestrator_state=orch_state,
            notes=notes,
        )
        self.last_decision = explanation
        if self.diagnostics is not None:
            self.diagnostics.log(
                "network_decision",
                details=redact(
                    {
                        "selected": explanation.selected_candidate,
                        "floor": explanation.service_floor,
                        "rejected": [r["candidate_id"] for r in rejected],
                    }
                ),
            )
        return explanation

    def _sync_orchestrator(
        self,
        selected: CandidatePath,
        admissible: list[tuple[CandidatePath, dict[str, float], list[str], float]],
    ) -> str:
        # Update orchestrator metrics from admissible candidates where bearer maps
        for c, scores, _flags, _u in admissible:
            kind = BEARER_TO_ORCH.get(c.normalized_bearer())
            if kind is None:
                continue
            m = BearerMetrics(
                available=bool(c.availability),
                signal_dbm=(c.signal_raw or {}).get("rssi_dbm"),
                latency_ms=c.latency_ms if c.latency_ms is not None else 9999.0,
                jitter_ms=c.jitter_ms if c.jitter_ms is not None else 9999.0,
                loss_pct=(c.packet_loss_ratio * 100.0) if c.packet_loss_ratio is not None else 100.0,
                cost_per_mb=c.monetary_cost if c.monetary_cost is not None else 1.0,
                energy_mw=c.energy_cost if c.energy_cost is not None else 1000.0,
                security_score=scores.get("security", 0.0),
                user_preference=scores.get("user_preference", 0.5),
            )
            try:
                self.orchestrator.update_metrics(kind, m)
            except ValueError:
                continue
        self.orchestrator.apply_decision_bearer(selected.normalized_bearer(), reason="wave005_decision")
        return self.orchestrator.state.value
