"""Export device state for 7gc-digital-twin scenarios."""
from __future__ import annotations

from .device_profile import get_profile
from .mode_manager import switch_mode
from .telemetry_contract import build_telemetry_packet


def export_seven_gc_device_state(device: str, mode: str) -> dict:
    ctx = switch_mode(device, mode)
    telemetry = build_telemetry_packet(device, mode)
    return {
        "site_id": "gary",
        "device_profile": get_profile(device, mode),
        "mode_context": ctx,
        "telemetry_stub": telemetry,
        "digital_twin_role": "synthetic_endpoint",
        "note": "research prototype — not field deployment",
    }
