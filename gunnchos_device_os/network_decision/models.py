"""Typed Anywhere objective / policy models (NET-ORCH-001)."""
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
    "LIVE_CARRIER_HANDOVER_VALIDATED": False,
    "PRODUCTION_NETWORK_OPTIMALITY": False,
    "FIELD_MEASURED_PERFORMANCE": False,
    "PRODUCTION_APP_PRIORITY_SIGNING": False,
}


class ServiceClass(str, Enum):
    EMERGENCY = "EMERGENCY"
    COMMUNICATION = "COMMUNICATION"
    LEARNING = "LEARNING"
    PRODUCTIVITY = "PRODUCTIVITY"
    CREATIVE = "CREATIVE"
    DEVELOPMENT = "DEVELOPMENT"
    ENTERTAINMENT = "ENTERTAINMENT"
    BACKGROUND_SYNC = "BACKGROUND_SYNC"


class ServiceFloor(str, Enum):
    IDEAL = "IDEAL"
    FULL = "FULL"
    REDUCED = "REDUCED"
    MINIMUM_USEFUL = "MINIMUM_USEFUL"
    OFFLINE_CAPABLE = "OFFLINE_CAPABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ApplicationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


class TrustLevel(str, Enum):
    UNTRUSTED = "UNTRUSTED"
    LIMITED = "LIMITED"
    TRUSTED = "TRUSTED"
    MANAGED = "MANAGED"


TRUST_RANK = {
    TrustLevel.UNTRUSTED: 0,
    TrustLevel.LIMITED: 1,
    TrustLevel.TRUSTED: 2,
    TrustLevel.MANAGED: 3,
}


class UserPreferenceProfile(str, Enum):
    BALANCED = "balanced"
    PREFER_PERFORMANCE = "prefer_performance"
    PREFER_LOW_COST = "prefer_low_cost"
    PREFER_BATTERY = "prefer_battery"
    PREFER_UNMETERED = "prefer_unmetered"
    PREFER_TRUSTED = "prefer_trusted"
    AVOID_CELLULAR = "avoid_cellular"
    AVOID_METERED = "avoid_metered"


class PrioritySource(str, Enum):
    SYSTEM_POLICY = "SYSTEM_POLICY"
    ADMIN_POLICY = "ADMIN_POLICY"
    FIRST_PARTY_SIGNED_MANIFEST = "FIRST_PARTY_SIGNED_MANIFEST"
    USER_REQUEST = "USER_REQUEST"
    APP_SELF_ASSERTED = "APP_SELF_ASSERTED"
    UNKNOWN = "UNKNOWN"


class EnforcementMode(str, Enum):
    SOFT = "SOFT"
    HARD = "HARD"


@dataclass
class PriorityAuthority:
    """Provenance for application priority — digital policy fixture, not production signing."""

    source: PrioritySource = PrioritySource.SYSTEM_POLICY
    issuer: str = "gunnchos.system_policy"
    trusted: bool = True
    policy_version: str = "wave005.v1"
    asserted_priority: ApplicationPriority = ApplicationPriority.NORMAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.value,
            "issuer": self.issuer,
            "trusted": self.trusted,
            "policy_version": self.policy_version,
            "asserted_priority": self.asserted_priority.value,
            "PRODUCTION_APP_PRIORITY_SIGNING": False,
            "label": "DIGITAL_POLICY_VALIDATION",
        }


@dataclass
class NetworkPreferencePolicy:
    """Persisted preference with optional HARD avoid rules (NET-ORCH-024)."""

    preference: UserPreferenceProfile = UserPreferenceProfile.BALANCED
    enforcement_mode: EnforcementMode = EnforcementMode.SOFT
    hard_avoid_bearers: set[str] = field(default_factory=set)
    hard_avoid_metered: bool = False
    profile_id: str = "default"
    policy_version: str = "wave005.pref.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "preference": self.preference.value,
            "enforcement_mode": self.enforcement_mode.value,
            "hard_avoid_bearers": sorted(self.hard_avoid_bearers),
            "hard_avoid_metered": self.hard_avoid_metered,
            "profile_id": self.profile_id,
            "policy_version": self.policy_version,
        }


class CostClass(str, Enum):
    UNMETERED = "unmetered"
    METERED = "metered"
    ESTIMATED_MARGINAL = "estimated_marginal_cost"
    ROAMING_HIGH = "roaming_high_cost"
    UNKNOWN = "unknown"


@dataclass
class MinimumUsefulService:
    max_latency_ms: float = 500.0
    max_jitter_ms: float = 80.0
    max_packet_loss: float = 0.15  # ratio 0..1
    min_availability: bool = True
    min_security: TrustLevel = TrustLevel.LIMITED
    min_signal: float = 0.15  # normalized 0..1


@dataclass
class ContinuityPolicy:
    allow_offline_fallback: bool = True
    max_telemetry_age_s: float = 30.0
    reject_future_timestamps: bool = True
    emergency_may_relax_energy: bool = True
    emergency_may_use_metered_hard_limit: bool = True
    battery_saving: bool = False


@dataclass
class DecisionConstraints:
    min_trust: TrustLevel = TrustLevel.LIMITED
    hard_prohibit_bearers: set[str] = field(default_factory=set)
    hard_prohibit_metered: bool = False
    require_unmetered_for_background: bool = False
    allow_emergency_data_exception: bool = True


@dataclass
class DecisionWeights:
    """Bounded weights for explainable utility. Units are relative importance."""

    availability: float = 1.0
    signal: float = 1.0
    latency: float = 1.2
    jitter: float = 1.0
    packet_loss: float = 1.3
    cost: float = 0.8
    energy: float = 0.7
    security: float = 1.0
    data: float = 0.9
    application_priority: float = 0.6
    user_preference: float = 0.8
    uncertainty: float = 0.5

    def clamped(self) -> "DecisionWeights":
        d = {}
        for k, v in asdict(self).items():
            try:
                fv = float(v)
            except (TypeError, ValueError):
                fv = 0.0
            if fv != fv or fv in (float("inf"), float("-inf")):  # NaN/inf
                fv = 0.0
            d[k] = max(0.0, min(5.0, fv))
        return DecisionWeights(**d)


@dataclass
class AnywhereServiceObjective:
    """NET-ORCH-001 runtime objective — thresholds are engineering config unless measured."""

    service_class: ServiceClass = ServiceClass.PRODUCTIVITY
    application_priority: ApplicationPriority = ApplicationPriority.NORMAL
    target_floor: ServiceFloor = ServiceFloor.FULL
    minimum_useful: MinimumUsefulService = field(default_factory=MinimumUsefulService)
    continuity: ContinuityPolicy = field(default_factory=ContinuityPolicy)
    constraints: DecisionConstraints = field(default_factory=DecisionConstraints)
    weights: DecisionWeights = field(default_factory=DecisionWeights)
    user_preference: UserPreferenceProfile = UserPreferenceProfile.BALANCED
    preference_policy: NetworkPreferencePolicy | None = None
    priority_authority: PriorityAuthority | None = None
    ideal_latency_ms: float = 50.0
    ideal_jitter_ms: float = 10.0
    ideal_packet_loss: float = 0.01
    notes: str = "engineering_configuration_thresholds"

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_class": self.service_class.value,
            "application_priority": self.application_priority.value,
            "target_floor": self.target_floor.value,
            "minimum_useful": asdict(self.minimum_useful) | {
                "min_security": self.minimum_useful.min_security.value
            },
            "continuity": asdict(self.continuity),
            "constraints": {
                "min_trust": self.constraints.min_trust.value,
                "hard_prohibit_bearers": sorted(self.constraints.hard_prohibit_bearers),
                "hard_prohibit_metered": self.constraints.hard_prohibit_metered,
                "require_unmetered_for_background": self.constraints.require_unmetered_for_background,
                "allow_emergency_data_exception": self.constraints.allow_emergency_data_exception,
            },
            "weights": asdict(self.weights.clamped()),
            "user_preference": self.user_preference.value,
            "preference_policy": None if self.preference_policy is None else self.preference_policy.to_dict(),
            "priority_authority": None if self.priority_authority is None else self.priority_authority.to_dict(),
            "ideal_latency_ms": self.ideal_latency_ms,
            "ideal_jitter_ms": self.ideal_jitter_ms,
            "ideal_packet_loss": self.ideal_packet_loss,
            "notes": self.notes,
            "claim_boundaries": dict(CLAIM_BOUNDARIES),
        }


def default_objective_for(service: ServiceClass) -> AnywhereServiceObjective:
    obj = AnywhereServiceObjective(service_class=service)
    if service == ServiceClass.EMERGENCY:
        obj.application_priority = ApplicationPriority.CRITICAL
        obj.priority_authority = PriorityAuthority(
            source=PrioritySource.SYSTEM_POLICY,
            issuer="gunnchos.system_policy.emergency",
            trusted=True,
            asserted_priority=ApplicationPriority.CRITICAL,
        )
        obj.minimum_useful.max_latency_ms = 800.0
        obj.minimum_useful.min_security = TrustLevel.LIMITED
        obj.weights.energy = 0.2
        obj.weights.cost = 0.2
        obj.weights.latency = 1.5
    elif service == ServiceClass.COMMUNICATION:
        obj.application_priority = ApplicationPriority.HIGH
        obj.minimum_useful.max_latency_ms = 200.0
        obj.minimum_useful.max_jitter_ms = 40.0
        obj.weights.jitter = 1.6
        obj.weights.latency = 1.5
    elif service == ServiceClass.BACKGROUND_SYNC:
        obj.application_priority = ApplicationPriority.BACKGROUND
        obj.constraints.require_unmetered_for_background = True
        obj.minimum_useful.max_latency_ms = 2000.0
        obj.minimum_useful.max_jitter_ms = 200.0
        obj.weights.cost = 1.5
        obj.weights.data = 1.4
        obj.weights.energy = 1.2
    elif service == ServiceClass.ENTERTAINMENT:
        obj.weights.latency = 1.3
        obj.weights.cost = 1.0
    return obj
