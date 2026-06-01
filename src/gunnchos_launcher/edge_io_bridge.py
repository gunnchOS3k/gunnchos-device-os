"""Bridge to edge-io-measurement-node telemetry contract (synthetic)."""
from __future__ import annotations

from .telemetry_contract import build_telemetry_packet


def export_edge_io_sample(device: str, mode: str) -> dict:
    sample = build_telemetry_packet(device, mode)
    return {
        "site_id": "gary",
        "telemetry": sample,
        "export_format": "seven_gc_compatible_stub",
    }
