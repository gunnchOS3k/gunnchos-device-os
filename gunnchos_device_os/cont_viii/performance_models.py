"""Performance / storage / memory / battery *models* only (Lane I).

No measured physical claims. Models are analytical envelopes for planning.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_PERF_MODELS_PASS


@dataclass(frozen=True)
class DeviceModel:
    sku: str
    cpu_tops_int8: float
    ram_gb: float
    storage_gb: float
    battery_wh: float
    idle_w: float
    active_w: float
    display_w: float


MODELS = (
    DeviceModel("student", 4.0, 8.0, 256.0, 40.0, 2.5, 8.0, 3.0),
    DeviceModel("ds_xl", 6.0, 16.0, 512.0, 55.0, 3.5, 12.0, 5.5),
    DeviceModel("handheld", 3.0, 8.0, 128.0, 25.0, 1.8, 6.5, 2.2),
    DeviceModel("dock_host", 8.0, 16.0, 512.0, 0.0, 5.0, 18.0, 0.0),
)


def estimate_battery_hours(m: DeviceModel, duty_active: float = 0.35) -> float | None:
    if m.battery_wh <= 0:
        return None
    avg_w = m.idle_w * (1 - duty_active) + (m.active_w + m.display_w) * duty_active
    if avg_w <= 0:
        return None
    return round(m.battery_wh / avg_w, 2)


def estimate_storage_headroom(m: DeviceModel, used_gb: float = 48.0) -> dict[str, float]:
    free = max(m.storage_gb - used_gb, 0.0)
    return {"capacity_gb": m.storage_gb, "used_gb": used_gb, "free_gb": free, "free_ratio": round(free / m.storage_gb, 3)}


def estimate_memory_pressure(m: DeviceModel, working_set_gb: float = 3.5) -> dict[str, Any]:
    headroom = m.ram_gb - working_set_gb
    return {
        "ram_gb": m.ram_gb,
        "working_set_gb": working_set_gb,
        "headroom_gb": round(headroom, 2),
        "pressure": "low" if headroom > 2 else ("moderate" if headroom > 0.5 else "high"),
    }


def evaluate_performance_models() -> dict[str, Any]:
    rows = []
    for m in MODELS:
        rows.append({
            "sku": m.sku,
            "cpu_tops_int8_model": m.cpu_tops_int8,
            "battery_hours_model": estimate_battery_hours(m),
            "storage": estimate_storage_headroom(m),
            "memory": estimate_memory_pressure(m),
            "power_envelope_w": {"idle": m.idle_w, "active": m.active_w, "display": m.display_w},
        })
    ok = len(rows) == len(MODELS)
    return {
        "schema": "gunnchos.performance_models.v1",
        "ok": ok,
        "token": TOKEN_PERF_MODELS_PASS if ok else None,
        "models": rows,
        "measured_physical": False,
        "bench_claimed": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY + " Models only — not lab measurements.",
    }
