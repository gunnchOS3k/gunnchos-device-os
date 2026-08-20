"""Typed continuity models and claim boundaries (Wave006 integrity repair)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


CLAIM_BOUNDARIES: dict[str, bool] = {
    "PHYSICAL_VALIDATION": False,
    "HUMAN_E6": False,
    "CARRIER_ACCEPTED": False,
    "STANDARDIZED_6G": False,
    "REAL_NTN_MODEM_VALIDATED": False,
    "FIELD_MEASURED_SATELLITE_VISIBILITY": False,
    "LIVE_CARRIER_HANDOVER_VALIDATED": False,
    "PRODUCTION_MPTCP_VALIDATED": False,
    "KERNEL_MPTCP_VALIDATED": False,
    "REAL_MPTCP": False,
    "PRODUCTION_NETWORK_OPTIMALITY": False,
    "UNIVERSAL_OPTIMALITY": False,
    "FIELD_MEASURED_PERFORMANCE": False,
    "PRODUCTION_APP_PRIORITY_SIGNING": False,
}


class ContinuityState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADING = "DEGRADING"
    TRANSITION_PREP = "TRANSITION_PREP"
    TRANSITIONING = "TRANSITIONING"
    RESUMING = "RESUMING"
    MULTIPATH = "MULTIPATH"
    REDUCED_SERVICE = "REDUCED_SERVICE"
    OFFLINE_CAPABLE = "OFFLINE_CAPABLE"
    RECOVERING = "RECOVERING"
    FAILED = "FAILED"
    # Compatibility aliases used by migration helpers
    DEGRADED = "REDUCED_SERVICE"
    OFFLINE = "OFFLINE_CAPABLE"


class ContinuityEvent(str, Enum):
    BANDWIDTH_DROP = "BANDWIDTH_DROP"
    BANDWIDTH_RECOVER = "BANDWIDTH_RECOVER"
    BEGIN_TRANSITION = "BEGIN_TRANSITION"
    TRANSITION_PREP_OK = "TRANSITION_PREP_OK"
    TRANSITION_COMMIT = "TRANSITION_COMMIT"
    TRANSITION_ROLLBACK = "TRANSITION_ROLLBACK"
    BEGIN_RESUME = "BEGIN_RESUME"
    RESUME_DONE = "RESUME_DONE"
    BEGIN_MULTIPATH = "BEGIN_MULTIPATH"
    MULTIPATH_DONE = "MULTIPATH_DONE"
    ENTER_OFFLINE = "ENTER_OFFLINE"
    BEGIN_RECOVERY = "BEGIN_RECOVERY"
    RECOVERY_DONE = "RECOVERY_DONE"
    FAIL = "FAIL"


class ContinuityAction(str, Enum):
    KEEP = "KEEP"
    TRANSITION = "TRANSITION"
    RESUME = "RESUME"
    MULTIPATH = "MULTIPATH"
    ADAPT = "ADAPT"
    CACHE_ONLY = "CACHE_ONLY"
    OPPORTUNISTIC_SYNC = "OPPORTUNISTIC_SYNC"
    RECOVER = "RECOVER"
    FAIL = "FAIL"


class SatelliteVisibilityProvenance(str, Enum):
    SIMULATED = "SIMULATED"
    DIGITAL_TWIN = "DIGITAL_TWIN"
    CONFIGURED_TARGET = "CONFIGURED_TARGET"
    UNKNOWN = "UNKNOWN"


class MultipathKind(str, Enum):
    APPLICATION_LEVEL_MULTIPATH = "APPLICATION_LEVEL_MULTIPATH"


class BearerClass(str, Enum):
    WIFI = "wifi"
    CELLULAR = "cellular"
    ETHERNET = "ethernet"
    NTN_SIMULATED = "ntn_simulated"
    LOCAL_INFRA = "local_infra"
    OFFLINE = "offline"


class LocalInfraStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class LocalCapability(str, Enum):
    INTERNET_SERVICE = "INTERNET_SERVICE"
    LOCAL_EDGE_SERVICE = "LOCAL_EDGE_SERVICE"
    LOCAL_CACHE_SERVICE = "LOCAL_CACHE_SERVICE"
    LOCAL_PEER_SERVICE = "LOCAL_PEER_SERVICE"


class AdaptationMode(str, Enum):
    FULL = "FULL"
    REDUCED = "REDUCED"
    MINIMUM_USEFUL = "MINIMUM_USEFUL"
    LOW_BANDWIDTH = "MINIMUM_USEFUL"  # alias
    EMERGENCY_MINIMAL = "EMERGENCY_MINIMAL"
    OFFLINE = "OFFLINE"


class TrafficClass(str, Enum):
    EMERGENCY = "EMERGENCY"
    LEARNING = "LEARNING"
    COMMUNICATION = "COMMUNICATION"
    BACKGROUND = "BACKGROUND"
    OTHER = "OTHER"


class TransitionPhase(str, Enum):
    PLANNED = "PLANNED"
    PREFLIGHT = "PREFLIGHT"
    TARGET_READY = "TARGET_READY"
    DRAINING_SOURCE = "DRAINING_SOURCE"
    ACTIVATING_TARGET = "ACTIVATING_TARGET"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


@dataclass
class SatelliteVisibilityWindow:
    candidate_id: str
    visible: bool
    window_start_utc: float
    window_end_utc: float
    expected_duration_s: float
    elevation_deg: float | None
    latency_estimate_ms: float | None
    confidence: float
    observed_or_generated_at: float
    max_age_s: float
    source: str
    source_repo: str
    source_commit: str
    provenance: SatelliteVisibilityProvenance
    satellites_in_view: int = 0
    note: str = "digital/synthetic visibility only; not real NTN modem"

    def is_fresh(self, now: float) -> bool:
        if self.provenance == SatelliteVisibilityProvenance.UNKNOWN:
            return False
        return (now - self.observed_or_generated_at) <= self.max_age_s

    def is_visible_now(self, now: float) -> bool:
        if not self.is_fresh(now):
            return False
        if self.provenance == SatelliteVisibilityProvenance.UNKNOWN:
            return False
        if self.elevation_deg is None:
            return False
        return (
            self.visible
            and self.window_start_utc <= now <= self.window_end_utc
            and self.elevation_deg >= 10.0
            and self.satellites_in_view >= 1
        )

    def remaining_window_s(self, now: float) -> float:
        if not self.is_visible_now(now):
            return 0.0
        return max(0.0, self.window_end_utc - now)

    def can_support_action(self, required_duration_s: float, now: float) -> bool:
        return self.remaining_window_s(now) >= required_duration_s

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = self.provenance.value
        d["REAL_NTN_MODEM_VALIDATED"] = False
        d["FIELD_MEASURED_SATELLITE_VISIBILITY"] = False
        return d


# Backward-compatible alias
SatelliteVisibility = SatelliteVisibilityWindow


@dataclass
class LocalInfrastructureSnapshot:
    link_or_ap_available: bool
    gateway_reachable: bool
    backhaul_reachable: bool
    dns_resolvable: bool
    edge_service_reachable: bool
    local_cache_available: bool
    peer_path_available: bool
    captive_portal_suspected: bool
    latency_ms: float | None
    observed_at: float
    max_age_s: float
    provenance: str = "DIGITAL_SYNTHETIC_EVIDENCE"
    note: str = "local infra capability graph (digital synthetic)"

    def is_fresh(self, now: float) -> bool:
        if self.provenance in ("UNKNOWN", ""):
            return False
        return (now - self.observed_at) <= self.max_age_s

    def capabilities(self, now: float) -> dict[str, bool]:
        if not self.is_fresh(now):
            return {c.value: False for c in LocalCapability}
        internet = (
            self.link_or_ap_available
            and self.gateway_reachable
            and self.backhaul_reachable
            and self.dns_resolvable
            and not self.captive_portal_suspected
        )
        return {
            LocalCapability.INTERNET_SERVICE.value: internet,
            LocalCapability.LOCAL_EDGE_SERVICE.value: self.edge_service_reachable and self.link_or_ap_available,
            LocalCapability.LOCAL_CACHE_SERVICE.value: self.local_cache_available,
            LocalCapability.LOCAL_PEER_SERVICE.value: self.peer_path_available,
        }

    def status(self, now: float) -> LocalInfraStatus:
        if not self.is_fresh(now) or self.provenance == "UNKNOWN":
            return LocalInfraStatus.UNKNOWN
        caps = self.capabilities(now)
        if caps[LocalCapability.INTERNET_SERVICE.value]:
            return LocalInfraStatus.AVAILABLE
        if any(
            caps[k]
            for k in (
                LocalCapability.LOCAL_EDGE_SERVICE.value,
                LocalCapability.LOCAL_CACHE_SERVICE.value,
                LocalCapability.LOCAL_PEER_SERVICE.value,
            )
        ):
            return LocalInfraStatus.DEGRADED
        return LocalInfraStatus.UNAVAILABLE

    def to_dict(self, now: float | None = None) -> dict[str, Any]:
        now = self.observed_at if now is None else now
        d = asdict(self)
        d["capabilities"] = self.capabilities(now)
        d["status"] = self.status(now).value
        return d


# Backward-compatible alias
LocalInfrastructureObservation = LocalInfrastructureSnapshot


@dataclass
class ServiceSession:
    schema_version: str
    checkpoint_id: str
    session_id: str
    service_id: str
    logical_position: int
    pending_operations: list[dict[str, Any]]
    committed_operation_ids: list[str]
    idempotency_keys: list[str]
    resume_token: str
    resume_token_expires_at: float
    cache_references: list[str]
    bearer_before_failure: str
    created_at: float
    updated_at: float
    resume_count: int = 0
    integrity_hash: str = ""
    # legacy fields kept for migration
    service_name: str = ""
    bearer: BearerClass = BearerClass.OFFLINE
    checkpoint: dict[str, Any] = field(default_factory=dict)
    sequence: int = 0
    continuity_state: ContinuityState = ContinuityState.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "service_id": self.service_id,
            "logical_position": self.logical_position,
            "pending_operations": list(self.pending_operations),
            "committed_operation_ids": list(self.committed_operation_ids),
            "idempotency_keys": list(self.idempotency_keys),
            "resume_token": self.resume_token,
            "resume_token_expires_at": self.resume_token_expires_at,
            "cache_references": list(self.cache_references),
            "bearer_before_failure": self.bearer_before_failure,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resume_count": self.resume_count,
            "integrity_hash": self.integrity_hash,
            "service_name": self.service_name or self.service_id,
            "bearer": self.bearer.value if isinstance(self.bearer, BearerClass) else self.bearer,
            "checkpoint": dict(self.checkpoint),
            "sequence": self.sequence,
            "continuity_state": self.continuity_state.value
            if isinstance(self.continuity_state, ContinuityState)
            else self.continuity_state,
        }


@dataclass
class DegradedModeReport:
    report_id: str
    service_id: str
    service_class: str
    state: ContinuityState
    selected_paths: list[str]
    reason_codes: list[str]
    lost_capabilities: list[str]
    retained_capabilities: list[str]
    current_adaptation_profile: str
    session_resume_available: bool
    cache_available: bool
    sync_deferred: bool
    pending_sync_items: int
    estimated_recovery_condition: str
    data_cost_warning: str | None
    security_warning: str | None
    provenance: str
    timestamp: float
    # legacy fields
    continuity_state: ContinuityState | None = None
    active_bearer: str | None = None
    adaptation_mode: AdaptationMode | None = None
    limitations: list[str] = field(default_factory=list)
    user_visible_message: str = ""
    claim_boundaries: dict[str, bool] = field(default_factory=lambda: dict(CLAIM_BOUNDARIES))
    transparent: bool = True

    def to_dict(self) -> dict[str, Any]:
        state = self.state or self.continuity_state or ContinuityState.FAILED
        return {
            "report_id": self.report_id,
            "service_id": self.service_id,
            "service_class": self.service_class,
            "state": state.value if isinstance(state, ContinuityState) else state,
            "continuity_state": state.value if isinstance(state, ContinuityState) else state,
            "selected_paths": list(self.selected_paths),
            "reason_codes": list(self.reason_codes),
            "lost_capabilities": list(self.lost_capabilities),
            "retained_capabilities": list(self.retained_capabilities),
            "current_adaptation_profile": self.current_adaptation_profile,
            "session_resume_available": self.session_resume_available,
            "cache_available": self.cache_available,
            "sync_deferred": self.sync_deferred,
            "pending_sync_items": self.pending_sync_items,
            "estimated_recovery_condition": self.estimated_recovery_condition,
            "data_cost_warning": self.data_cost_warning,
            "security_warning": self.security_warning,
            "provenance": self.provenance,
            "timestamp": self.timestamp,
            "active_bearer": self.active_bearer,
            "adaptation_mode": (
                self.adaptation_mode.value
                if isinstance(self.adaptation_mode, AdaptationMode)
                else self.current_adaptation_profile
            ),
            "limitations": list(self.limitations),
            "user_visible_message": self.user_visible_message,
            "transparent": self.transparent,
            "claim_boundaries": dict(self.claim_boundaries),
            "shell_projection": {
                "headline": self.user_visible_message,
                "what_still_works": list(self.retained_capabilities),
                "what_temporarily_unavailable": list(self.lost_capabilities),
                "work_safe_locally": self.cache_available or "LOCAL" in " ".join(self.retained_capabilities),
                "changes_pending_sync": self.sync_deferred or self.pending_sync_items > 0,
                "recovery_condition": self.estimated_recovery_condition,
                "security_or_metered_warning": self.security_warning or self.data_cost_warning,
            },
        }
