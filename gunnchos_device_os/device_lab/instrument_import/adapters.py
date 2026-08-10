"""CSV/JSON instrument import adapters for EVT evidence ingestion."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Callable


def _generic_json(payload: str | dict[str, Any]) -> dict[str, Any]:
    data = json.loads(payload) if isinstance(payload, str) else dict(payload)
    return {
        "adapter": "generic_json",
        "instrument_id": data.get("instrument_id") or data.get("instrument"),
        "instrument_serial": data.get("instrument_serial") or data.get("serial"),
        "measurement": data.get("measurement", data.get("value")),
        "unit": data.get("unit"),
        "timestamp_utc": data.get("timestamp_utc") or data.get("timestamp"),
        "raw": data,
        "calibration_status": data.get("calibration_status", "PENDING_PHYSICAL"),
        "vf_status": "PHYSICAL_PENDING",
    }


def _generic_csv(payload: str) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(payload))
    rows = list(reader)
    if not rows:
        raise ValueError("empty CSV instrument payload")
    row = rows[0]
    return {
        "adapter": "generic_csv",
        "instrument_id": row.get("instrument_id") or row.get("instrument"),
        "instrument_serial": row.get("instrument_serial") or row.get("serial"),
        "measurement": _maybe_float(row.get("measurement") or row.get("value")),
        "unit": row.get("unit"),
        "timestamp_utc": row.get("timestamp_utc") or row.get("timestamp"),
        "raw_rows": rows,
        "calibration_status": row.get("calibration_status", "PENDING_PHYSICAL"),
        "vf_status": "PHYSICAL_PENDING",
    }


def _pd_analyzer_json(payload: str | dict[str, Any]) -> dict[str, Any]:
    base = _generic_json(payload)
    raw = base["raw"]
    base["adapter"] = "usb_pd_analyzer_json"
    base["measurement"] = raw.get("contract_w", base.get("measurement"))
    base["unit"] = "W"
    base["suggested_physical_test_id"] = "EVT-DOCK-001"
    base["suggested_metric_id"] = "pd_contract"
    return base


def _thermocouple_csv(payload: str) -> dict[str, Any]:
    base = _generic_csv(payload)
    base["adapter"] = "thermocouple_logger_csv"
    # Prefer skin channel if present
    for row in base["raw_rows"]:
        if (row.get("channel") or "").lower() in {"skin", "skin_temp", "t_skin"}:
            base["measurement"] = _maybe_float(row.get("measurement") or row.get("value") or row.get("temp_c"))
            break
    base["unit"] = "C"
    base["suggested_physical_test_id"] = "EVT-THERM-001"
    base["suggested_metric_id"] = "skin_temp"
    return base


def _current_probe_csv(payload: str) -> dict[str, Any]:
    base = _generic_csv(payload)
    base["adapter"] = "current_probe_csv"
    base["unit"] = base.get("unit") or "A"
    base["suggested_physical_test_id"] = "EVT-PWR-004"
    base["suggested_metric_id"] = "pin"
    return base


def _maybe_float(v: Any) -> Any:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


ADAPTERS: dict[str, Callable[[Any], dict[str, Any]]] = {
    "generic_json": _generic_json,
    "generic_csv": _generic_csv,
    "usb_pd_analyzer_json": _pd_analyzer_json,
    "thermocouple_logger_csv": _thermocouple_csv,
    "current_probe_csv": _current_probe_csv,
}


def list_adapters() -> list[str]:
    return sorted(ADAPTERS)


def import_instrument_payload(adapter: str, payload: Any) -> dict[str, Any]:
    if adapter not in ADAPTERS:
        raise KeyError(f"unknown instrument adapter: {adapter}")
    out = ADAPTERS[adapter](payload)
    out["CALIBRATED_EVT0"] = False
    out["vf_status"] = "PHYSICAL_PENDING"
    return out
