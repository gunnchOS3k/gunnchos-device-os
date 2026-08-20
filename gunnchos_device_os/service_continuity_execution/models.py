"""Typed continuity models and claim boundaries (Wave006)."""
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
    "KERNEL_MPTCP_VALIDATED": False,
    "REAL_MPTCP": False,
    "PRODUCTION_NETWORK_OPTIMALITY": False,
    "UNIVERSAL_OPTIMALITY": False,
    "FIELD_MEASURED_PERFORMANCE": False,
    "PRODUCTION_APP_PRIORITY_SIGNING": False,
}


class ContinuityState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    TRANSITIONING = "TRANSITIONING"
    RESUMING = "RESUMING"
    OFFLINE = "OFFLINE"
    FAILED = "FAILED"


class SatelliteVisibilityProvenance(str, Enum):
    SIMULATED = "SIMULATED"
    DIGITAL_TWIN = "DIGITAL_TWIN"
    UNKNOWN = "UNKNOWN"


class MultipathKind(str, Enum):
    APPLICATION_LEVEL_MULTIPATH = "APPLICATION_LEVEL_MULTIPATH"
    # Explicitly not claimed:
    # KERNEL_MPTCP / CARRIER_MPTCP


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


class AdaptationMode(str, Enum):
    FULL = "FULL"
    REDUCED = "REDUCED"
    LOW_BANDWIDTH = "LOW_BANDWIDTH"
    EMERGENCY_MINIMAL = "EMERGENCY_MINIMAL"
    OFFLINE = "OFFLINE"


class TrafficClass(str, Enum):
    EMERGENCY = "EMERGENCY"
    LEARNING = "LEARNING"
    COMMUNICATION = "COMMUNICATION"
    BACKGROUND = "BACKGROUND"
    OTHER = "OTHER"


@dataclass
class SatelliteVisibility:
    visible: bool
    elevation_deg: float | None
    satellites_in_view: int
    provenance: SatelliteVisibilityProvenance
    confidence: float
    note: str = "digital/synthetic visibility only; not real NTN modem"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = self.provenance.value
        d["REAL_NTN_MODEM_VALIDATED"] = False
        return d


@dataclass
class LocalInfrastructureObservation:
    status: LocalInfraStatus
    gateway_reachable: bool
    dns_resolvable: bool
    captive_portal_suspected: bool
    latency_ms: float | None
    provenance: str = "DIGITAL_SYNTHETIC_EVIDENCE"
    note: str = "local infra status is software-observed digital evidence"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class ServiceSession:
    session_id: str
    service_name: str
    bearer: BearerClass
    checkpoint: dict[str, Any] = field(default_factory=dict)
    sequence: int = 0
    continuity_state: ContinuityState = ContinuityState.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "service_name": self.service_name,
            "bearer": self.bearer.value,
            "checkpoint": dict(self.checkpoint),
            "sequence": self.sequence,
            "continuity_state": self.continuity_state.value,
        }


@dataclass
class DegradedModeReport:
    continuity_state: ContinuityState
    active_bearer: str | None
    adaptation_mode: AdaptationMode
    limitations: list[str]
    user_visible_message: str
    claim_boundaries: dict[str, bool] = field(default_factory=lambda: dict(CLAIM_BOUNDARIES))
    transparent: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "continuity_state": self.continuity_state.value,
            "active_bearer": self.active_bearer,
            "adaptation_mode": self.adaptation_mode.value,
            "limitations": list(self.limitations),
            "user_visible_message": self.user_visible_message,
            "transparent": self.transparent,
            "claim_boundaries": dict(self.claim_boundaries),
        }
