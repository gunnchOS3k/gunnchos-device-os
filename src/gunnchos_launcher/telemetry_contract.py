"""Privacy-safe telemetry packet (synthetic)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .qos_policy import get_qos_profile


def build_telemetry_packet(device: str, mode: str, opt_in: bool = True) -> dict:
    if not opt_in:
        raise ValueError("Telemetry requires opt_in=True")
    ts = datetime.now(timezone.utc).isoformat()
    device_hash = hashlib.sha256(device.encode()).hexdigest()[:16]
    qos = get_qos_profile("urllc_strict" if mode == "play" else "balanced")
    return {
        "device_id_hash": device_hash,
        "timestamp_iso": ts,
        "mode": mode,
        "latency_ms": 12.5,
        "jitter_ms": 1.2,
        "packet_loss_pct": 0.05,
        "qos_preset": qos["name"],
        "privacy_tier": "synthetic_tier_a",
        "consent_state": "opt_in_active",
        "note": "synthetic mock — aligns with edge-io-measurement-node schema concepts",
    }
