"""Performance model schema — HOST_OBSERVED vs MODELED vs PHYSICAL_MEASURED."""
from __future__ import annotations

from typing import Any


SCHEMA = {
    "schema": "gunnchos.device_lab.performance_model.v1",
    "metrics": [
        "cpu_budget",
        "ram",
        "memory_bandwidth_assumption",
        "gpu_class_budget",
        "npu_model_budget",
        "storage_throughput",
        "network_envelope",
        "power_states",
        "thermal_envelope",
        "display_refresh",
    ],
    "result_kinds": [
        "HOST_OBSERVED",
        "VIRTUAL_CONSTRAINED",
        "MODELED_TARGET_RANGE",
        "CALIBRATED_TARGET",
        "PHYSICAL_MEASURED",
    ],
    "ranges": ["BEST_CASE", "EXPECTED", "THERMALLY_CONSTRAINED", "WORST_ACCEPTABLE"],
    "pre_EVT": {
        "CALIBRATED_TARGET": "unavailable",
        "PHYSICAL_MEASURED": "unavailable",
    },
}


def performance_snapshot(host_observed: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        **SCHEMA,
        "HOST_OBSERVED": host_observed or {},
        "MODELED_TARGET_RANGE": {
            "status": "FOUNDATION_SCHEMA_ONLY",
            "note": "Do not claim exact physical FPS/battery/RF/thermals/NPU",
        },
        "CALIBRATED_TARGET": None,
        "PHYSICAL_MEASURED": None,
        "claim_boundary": "Modeled numbers are not physical measurements.",
    }
