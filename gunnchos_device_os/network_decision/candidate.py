"""Candidate path model with honest bearer labels and provenance."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from gunnchos_device_os.network_decision.models import CostClass, TrustLevel


class TelemetryProvenance(str, Enum):
    HOST_OBSERVED = "HOST_OBSERVED"
    DEVICE_OBSERVED = "DEVICE_OBSERVED"
    DIGITAL_TWIN = "DIGITAL_TWIN"
    SIMULATED = "SIMULATED"
    CONFIGURED_TARGET = "CONFIGURED_TARGET"
    UNKNOWN = "UNKNOWN"
    DIGITAL_SYNTHETIC_EVIDENCE = "DIGITAL_SYNTHETIC_EVIDENCE"


HONEST_BEARERS = frozenset({
    "ethernet",
    "wifi",
    "cellular_generic",
    "peer_local",
    "ntn_simulated",
    "offline",
})


def _finite_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


@dataclass
class CandidatePath:
    candidate_id: str
    bearer_class: str
    availability: bool | None = None
    signal_quality: float | None = None  # normalized preference if already 0..1
    signal_raw: dict[str, Any] = field(default_factory=dict)  # rssi/rsrp/etc
    latency_ms: float | None = None
    jitter_ms: float | None = None
    packet_loss_ratio: float | None = None  # 0..1 canonical
    monetary_cost: float | None = None  # relative; None => unknown
    cost_class: CostClass = CostClass.UNKNOWN
    energy_cost: float | None = None  # modeled mW-equivalent; None => unknown
    energy_modeled: bool = True
    security_trust: TrustLevel = TrustLevel.UNTRUSTED
    data_unlimited: bool = False
    data_remaining_bytes: int | None = None
    data_remaining_fraction: float | None = None
    data_hard_limit: bool = False
    data_soft_limit: bool = False
    data_metered: bool = False
    application_compatibility: bool = True
    telemetry_timestamp: float | None = None  # unix epoch seconds
    telemetry_source: TelemetryProvenance = TelemetryProvenance.UNKNOWN
    confidence: float | None = None  # 0..1
    admin_prohibited: bool = False
    roaming_high_cost: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def normalized_bearer(self) -> str:
        b = (self.bearer_class or "").strip().lower()
        aliases = {
            "cellular": "cellular_generic",
            "bt": "peer_local",
            "bluetooth": "peer_local",
            "pan": "peer_local",
            "ntn": "ntn_simulated",
        }
        return aliases.get(b, b)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["bearer_class"] = self.normalized_bearer()
        d["cost_class"] = self.cost_class.value
        d["security_trust"] = self.security_trust.value
        d["telemetry_source"] = self.telemetry_source.value
        d["STANDARDIZED_6G"] = False
        d["CARRIER_ACCEPTED"] = False
        d["REAL_NTN_MODEM_VALIDATED"] = False
        return d


def sanitize_candidate(raw: CandidatePath, *, now_ts: float) -> tuple[CandidatePath, list[str]]:
    """Return a sanitized copy plus invalidation flags. Never treat invalid as best-case."""
    flags: list[str] = []
    c = CandidatePath(**{**asdict(raw), "signal_raw": dict(raw.signal_raw), "extra": dict(raw.extra)})
    c.bearer_class = c.normalized_bearer()
    if c.bearer_class not in HONEST_BEARERS:
        flags.append("unknown_bearer_class")
        c.application_compatibility = False

    # availability contradiction
    if c.availability is True and c.bearer_class == "offline":
        # offline sink is always "available" as fallback — ok
        pass
    if c.availability is True and c.packet_loss_ratio is not None:
        pl = _finite_or_none(c.packet_loss_ratio)
        if pl is not None and pl >= 1.0 and c.bearer_class != "offline":
            flags.append("contradictory_availability_total_loss")
            c.availability = False

    # latency
    lat = _finite_or_none(c.latency_ms)
    if c.latency_ms is not None and lat is None:
        flags.append("invalid_latency")
        c.latency_ms = None
    elif lat is not None and lat < 0:
        flags.append("negative_latency")
        c.latency_ms = None
    else:
        c.latency_ms = lat

    # jitter
    jit = _finite_or_none(c.jitter_ms)
    if c.jitter_ms is not None and jit is None:
        flags.append("invalid_jitter")
        c.jitter_ms = None
    elif jit is not None and jit < 0:
        flags.append("negative_jitter")
        c.jitter_ms = None
    else:
        c.jitter_ms = jit

    # packet loss
    pl = _finite_or_none(c.packet_loss_ratio)
    if c.packet_loss_ratio is not None and pl is None:
        flags.append("invalid_packet_loss")
        c.packet_loss_ratio = None
    elif pl is not None and (pl < 0 or pl > 1):
        flags.append("packet_loss_out_of_range")
        c.packet_loss_ratio = None
    else:
        c.packet_loss_ratio = pl

    # signal
    sq = _finite_or_none(c.signal_quality)
    if c.signal_quality is not None and sq is None:
        flags.append("invalid_signal")
        c.signal_quality = None
    elif sq is not None and (sq < 0 or sq > 1):
        flags.append("signal_out_of_range")
        c.signal_quality = None
    else:
        c.signal_quality = sq

    # cost/energy unknowns stay None
    cost = _finite_or_none(c.monetary_cost)
    if c.monetary_cost is not None and cost is None:
        flags.append("invalid_cost")
        c.monetary_cost = None
        c.cost_class = CostClass.UNKNOWN
    else:
        c.monetary_cost = cost

    energy = _finite_or_none(c.energy_cost)
    if c.energy_cost is not None and energy is None:
        flags.append("invalid_energy")
        c.energy_cost = None
    elif energy is not None and energy < 0:
        flags.append("negative_energy")
        c.energy_cost = None
    else:
        c.energy_cost = energy

    conf = _finite_or_none(c.confidence)
    if c.confidence is not None and conf is None:
        flags.append("invalid_confidence")
        c.confidence = None
    elif conf is not None:
        c.confidence = max(0.0, min(1.0, conf))
    else:
        c.confidence = conf

    # timestamps
    ts = _finite_or_none(c.telemetry_timestamp)
    if c.telemetry_timestamp is not None and ts is None:
        flags.append("invalid_timestamp")
        c.telemetry_timestamp = None
    else:
        c.telemetry_timestamp = ts
        if ts is not None:
            if ts > now_ts + 1.0:
                flags.append("future_timestamp")
            if now_ts - ts > 1e7:  # absurdly old still ok as stale later
                pass

    if c.security_trust not in TrustLevel:
        flags.append("unknown_security")
        c.security_trust = TrustLevel.UNTRUSTED

    return c, flags
