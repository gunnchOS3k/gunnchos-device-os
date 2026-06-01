"""Research measurement mode session (synthetic)."""
from __future__ import annotations

from .edge_io_bridge import export_edge_io_sample
from .seven_gc_bridge import export_seven_gc_device_state


def run_measurement_session(device: str, duration_s: int = 30) -> dict:
    mode = "research_measurement"
    return {
        "device": device,
        "mode": mode,
        "duration_s": duration_s,
        "edge_io_export": export_edge_io_sample(device, mode),
        "seven_gc_export": export_seven_gc_device_state(device, mode),
        "status": "completed_synthetic",
    }
