"""Priority authority resolution for NET-ORCH-023."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from gunnchos_device_os.network_decision.candidate import CandidatePath, TelemetryProvenance
from gunnchos_device_os.network_decision.engine import AnywhereNetworkDecisionEngine
from gunnchos_device_os.network_decision.models import (
    ApplicationPriority,
    CostClass,
    PriorityAuthority,
    PrioritySource,
    ServiceClass,
    TrustLevel,
    UserPreferenceProfile,
    default_objective_for,
)

NOW = 1_700_000_000.0

TRUSTED_SOURCES = frozenset({
    PrioritySource.SYSTEM_POLICY,
    PrioritySource.ADMIN_POLICY,
    PrioritySource.FIRST_PARTY_SIGNED_MANIFEST,
})


def resolve_priority_authority(
    asserted: ApplicationPriority,
    authority: PriorityAuthority | None,
) -> dict[str, Any]:
    """Apply provenance rules. CRITICAL requires trusted authority."""
    if authority is None:
        authority = PriorityAuthority(
            source=PrioritySource.UNKNOWN,
            issuer="missing",
            trusted=False,
            asserted_priority=asserted,
        )
    effective = asserted
    action = "accepted"
    reasons: list[str] = []
    trusted = bool(authority.trusted) and authority.source in TRUSTED_SOURCES

    if asserted in {ApplicationPriority.CRITICAL, ApplicationPriority.HIGH}:
        if authority.source == PrioritySource.APP_SELF_ASSERTED:
            effective = ApplicationPriority.NORMAL
            action = "downgraded"
            reasons.append("APP_SELF_ASSERTED_CRITICAL_OR_HIGH_REJECTED")
            trusted = False
        elif authority.source == PrioritySource.UNKNOWN or not trusted:
            if asserted == ApplicationPriority.CRITICAL:
                effective = ApplicationPriority.NORMAL
                action = "downgraded"
                reasons.append("UNTRUSTED_OR_UNKNOWN_AUTHORITY_CANNOT_ELEVATE_CRITICAL")
                trusted = False
            else:
                # HIGH may proceed under bounded policy but is not emergency-class
                reasons.append("HIGH_WITHOUT_TRUSTED_AUTHORITY_BOUNDED")
        elif authority.asserted_priority != asserted and authority.source in TRUSTED_SOURCES:
            # trusted issuer may still clamp to its asserted_priority
            effective = authority.asserted_priority
            action = "authority_clamped"
            reasons.append("AUTHORITY_ASSERTED_PRIORITY_APPLIED")
    return {
        "asserted": asserted.value,
        "effective": effective.value,
        "action": action,
        "trusted": trusted,
        "reasons": reasons,
        "authority": authority.to_dict(),
        "PRODUCTION_APP_PRIORITY_SIGNING": False,
    }


def apply_priority_to_objective(obj, authority: PriorityAuthority | None = None):
    """Mutate objective.application_priority via authority resolution."""
    auth = authority if authority is not None else obj.priority_authority
    resolved = resolve_priority_authority(obj.application_priority, auth)
    obj.application_priority = ApplicationPriority(resolved["effective"])
    obj.priority_authority = auth or PriorityAuthority(
        source=PrioritySource.UNKNOWN,
        trusted=False,
        asserted_priority=ApplicationPriority(resolved["asserted"]),
    )
    return resolved


def _boundary_candidates() -> list[CandidatePath]:
    """Near-parity paths: low-energy/high-latency vs high-energy/low-latency (same cost/security)."""
    return [
        CandidatePath(
            candidate_id="sip-path",
            bearer_class="wifi",
            availability=True,
            signal_quality=0.80,
            latency_ms=90.0,
            jitter_ms=12.0,
            packet_loss_ratio=0.015,
            monetary_cost=0.0,
            cost_class=CostClass.UNMETERED,
            energy_cost=120.0,
            security_trust=TrustLevel.TRUSTED,
            data_unlimited=True,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1.0,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.92,
        ),
        CandidatePath(
            candidate_id="fast-path",
            bearer_class="wifi",
            availability=True,
            signal_quality=0.80,
            latency_ms=12.0,
            jitter_ms=2.0,
            packet_loss_ratio=0.008,
            monetary_cost=0.0,
            cost_class=CostClass.UNMETERED,
            energy_cost=1400.0,
            security_trust=TrustLevel.TRUSTED,
            data_unlimited=True,
            application_compatibility=True,
            telemetry_timestamp=NOW - 1.0,
            telemetry_source=TelemetryProvenance.DIGITAL_SYNTHETIC_EVIDENCE,
            confidence=0.92,
        ),
    ]


def _inputs_hash(cands: list[CandidatePath]) -> str:
    payload = [c.to_dict() for c in cands]
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def prove_priority_only_boundary() -> dict[str, Any]:
    cands = _boundary_candidates()
    h = _inputs_hash(cands)

    obj_bg = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj_bg.application_priority = ApplicationPriority.BACKGROUND
    obj_bg.user_preference = UserPreferenceProfile.BALANCED
    obj_bg.continuity.battery_saving = False
    obj_bg.priority_authority = PriorityAuthority(
        source=PrioritySource.SYSTEM_POLICY,
        trusted=True,
        asserted_priority=ApplicationPriority.BACKGROUND,
    )
    apply_priority_to_objective(obj_bg)
    d_bg = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(cands, obj_bg)

    obj_crit = default_objective_for(ServiceClass.PRODUCTIVITY)
    obj_crit.application_priority = ApplicationPriority.CRITICAL
    obj_crit.user_preference = UserPreferenceProfile.BALANCED
    obj_crit.continuity.battery_saving = False
    obj_crit.constraints.min_trust = TrustLevel.TRUSTED
    obj_crit.priority_authority = PriorityAuthority(
        source=PrioritySource.SYSTEM_POLICY,
        issuer="gunnchos.system_policy",
        trusted=True,
        asserted_priority=ApplicationPriority.CRITICAL,
    )
    apply_priority_to_objective(obj_crit)
    d_crit = AnywhereNetworkDecisionEngine(now_fn=lambda: NOW).decide(cands, obj_crit)

    selection_changed = d_bg.selected_candidate != d_crit.selected_candidate
    ok = (
        d_bg.selected_candidate == "sip-path"
        and d_crit.selected_candidate == "fast-path"
        and selection_changed
        and h == _inputs_hash(cands)
    )
    return {
        "schema": "gunnchos.engineering_wave005.application_priority_boundary.v1",
        "ok": ok,
        "candidate_inputs_hash_same": True,
        "candidate_inputs_hash": h,
        "priority_a": ApplicationPriority.BACKGROUND.value,
        "selected_a": d_bg.selected_candidate,
        "priority_b": ApplicationPriority.CRITICAL.value,
        "selected_b": d_crit.selected_candidate,
        "selection_changed": selection_changed,
        "score_breakdown_a": {
            "final_scores": d_bg.final_scores,
            "weights": d_bg.weights,
        },
        "score_breakdown_b": {
            "final_scores": d_crit.final_scores,
            "weights": d_crit.weights,
        },
        "label": "DIGITAL_SYNTHETIC_EVIDENCE",
    }


def prove_self_asserted_critical_blocked() -> dict[str, Any]:
    resolved = resolve_priority_authority(
        ApplicationPriority.CRITICAL,
        PriorityAuthority(
            source=PrioritySource.APP_SELF_ASSERTED,
            issuer="com.example.self",
            trusted=False,
            asserted_priority=ApplicationPriority.CRITICAL,
        ),
    )
    unknown = resolve_priority_authority(
        ApplicationPriority.CRITICAL,
        PriorityAuthority(
            source=PrioritySource.UNKNOWN,
            issuer="unknown",
            trusted=False,
            asserted_priority=ApplicationPriority.CRITICAL,
        ),
    )
    ok = (
        resolved["effective"] != ApplicationPriority.CRITICAL.value
        and unknown["effective"] != ApplicationPriority.CRITICAL.value
        and resolved["action"] == "downgraded"
    )
    return {
        "schema": "gunnchos.engineering_wave005.application_priority_authority.v1",
        "ok": ok,
        "self_asserted": resolved,
        "unknown_authority": unknown,
        "PRODUCTION_APP_PRIORITY_SIGNING": False,
        "label": "DIGITAL_POLICY_VALIDATION",
    }
