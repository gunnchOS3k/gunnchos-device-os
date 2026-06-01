"""QoS traffic-class profiles (conceptual; OS integration future work)."""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class QosProfile:
    name: str
    latency_target_ms: float
    jitter_target_ms: float
    packet_loss_target_pct: float
    traffic_classes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


PRESETS = {
    "urllc_strict": QosProfile("urllc_strict", 10.0, 2.0, 0.1, ["interactive", "control"]),
    "balanced": QosProfile("balanced", 50.0, 10.0, 1.0, ["default", "bulk"]),
    "school_safe": QosProfile("school_safe", 80.0, 15.0, 2.0, ["education", "admin"]),
}


def get_qos_profile(preset: str) -> dict:
    if preset not in PRESETS:
        raise ValueError(preset)
    return PRESETS[preset].to_dict()
