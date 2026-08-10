"""Device Lab measurement/calibration interfaces for WP-010.

Provides schemas and helpers for:
- physical test ID validation
- calibration ingestion (records only; no CALIBRATED_* tokens pre-EVT)
- metric mapping (Lab prediction metric_id ↔ EVT physical metric)
- prediction-vs-measurement comparison
- evidence linkage
- instrument import adapters

Does NOT promote VF4/VF5/VF6. Does NOT execute LAB-FUTURE-007/008/009.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PHYSICAL_TEST_ID_RE = re.compile(r"^EVT-[A-Z]+-[0-9]{3}$")

CALIBRATION_CONTRACT_SCHEMA = {
    "schema": "gunnchos.device_lab.calibration_contract.v1",
    "fields": [
        "virtual_run_id",
        "physical_test_id",
        "configuration_id",
        "metric",
        "virtual_prediction",
        "physical_measurement",
        "absolute_error",
        "relative_error",
        "confidence_interval",
        "calibration_version",
    ],
    "tokens_forbidden_pre_EVT": True,
}

FORBIDDEN_CALIBRATION_TOKENS = {
    "CALIBRATED_EVT0",
    "CALIBRATED_TARGET",
    "PHYSICAL_CORRELATION_PASS",
}

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def calibration_status() -> dict[str, Any]:
    return {
        **CALIBRATION_CONTRACT_SCHEMA,
        "CALIBRATED_EVT0": False,
        "status": "PHYSICAL_PENDING",
        "VF4": "PHYSICAL_PENDING",
        "VF5": "PHYSICAL_PENDING",
        "VF6": "PHYSICAL_PENDING",
        "note": "No calibration token may be set before real EVT measurements.",
        "wp010_interfaces": "READY_SCHEMA_ONLY",
    }


def assert_no_calibration_token(payload: dict[str, Any]) -> None:
    for k in FORBIDDEN_CALIBRATION_TOKENS:
        if payload.get(k) in (True, "PASS", "CALIBRATED"):
            raise AssertionError(f"calibration token {k} forbidden without EVT")


def validate_physical_test_id(test_id: str) -> str:
    if not PHYSICAL_TEST_ID_RE.match(test_id):
        raise ValueError(f"invalid physical_test_id: {test_id!r}")
    return test_id


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text())


def ingest_calibration_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize an ingestion record. Never sets CALIBRATED_*."""
    assert_no_calibration_token(record)
    required = [
        "virtual_run_id",
        "physical_test_id",
        "metric_id",
        "prediction",
        "measurement",
        "calibration_version",
    ]
    missing = [k for k in required if k not in record]
    if missing:
        raise ValueError(f"calibration ingestion missing fields: {missing}")
    validate_physical_test_id(record["physical_test_id"])
    out = dict(record)
    out.setdefault("vf_status", "PHYSICAL_PENDING")
    out["vf_status"] = "PHYSICAL_PENDING"
    out["CALIBRATED_EVT0"] = False
    out["ingestion_status"] = "ACCEPTED_PENDING_PHYSICAL_CORRELATION"
    if out.get("measurement") is None:
        out["ingestion_status"] = "SCHEMA_ONLY_NO_MEASUREMENT"
    return out


def map_metric(lab_metric_id: str, physical_metric_id: str | None = None) -> dict[str, Any]:
    """Map Device Lab metric ids to EVT physical metric ids."""
    table = DEFAULT_METRIC_MAP
    if lab_metric_id in table:
        row = dict(table[lab_metric_id])
        if physical_metric_id and physical_metric_id != row["physical_metric_id"]:
            raise ValueError(
                f"metric map mismatch for {lab_metric_id}: "
                f"{physical_metric_id} != {row['physical_metric_id']}"
            )
        return row
    if physical_metric_id:
        return {
            "lab_metric_id": lab_metric_id,
            "physical_metric_id": physical_metric_id,
            "unit": None,
            "status": "AD_HOC_UNVERIFIED",
        }
    raise KeyError(f"unknown lab_metric_id: {lab_metric_id}")


DEFAULT_METRIC_MAP: dict[str, dict[str, Any]] = {
    "lab.dock.pd_contract_w": {
        "lab_metric_id": "lab.dock.pd_contract_w",
        "physical_metric_id": "pd_contract",
        "physical_test_id": "EVT-DOCK-001",
        "unit": "W",
        "golden_journeys": ["GOLDEN-04", "GOLDEN-05"],
    },
    "lab.dock.hotplug_reconnect_ms": {
        "lab_metric_id": "lab.dock.hotplug_reconnect_ms",
        "physical_metric_id": "hotplug_reconnect_ms",
        "physical_test_id": "EVT-DOCK-003",
        "unit": "ms",
        "golden_journeys": ["GOLDEN-04", "GOLDEN-05"],
    },
    "lab.dsxl.dual_display_count": {
        "lab_metric_id": "lab.dsxl.dual_display_count",
        "physical_metric_id": "dual_display_enum",
        "physical_test_id": "EVT-DISP-002",
        "unit": "count",
        "golden_journeys": ["GOLDEN-06"],
    },
    "lab.ring.e2e_latency_ms": {
        "lab_metric_id": "lab.ring.e2e_latency_ms",
        "physical_metric_id": "e2e_latency",
        "physical_test_id": "EVT-RING-002",
        "unit": "ms",
        "golden_journeys": ["GOLDEN-07"],
    },
    "lab.ring.pose_error": {
        "lab_metric_id": "lab.ring.pose_error",
        "physical_metric_id": "pose_error",
        "physical_test_id": "EVT-RING-003",
        "unit": "mm_or_deg",
        "golden_journeys": ["GOLDEN-07"],
    },
    "lab.ai.ttft_ms": {
        "lab_metric_id": "lab.ai.ttft_ms",
        "physical_metric_id": "ttft",
        "physical_test_id": "EVT-AI-001",
        "unit": "ms",
        "golden_journeys": ["GOLDEN-08"],
    },
    "lab.ai.tokens_per_s": {
        "lab_metric_id": "lab.ai.tokens_per_s",
        "physical_metric_id": "tokens_per_s",
        "physical_test_id": "EVT-AI-001",
        "unit": "tok/s",
        "golden_journeys": ["GOLDEN-08"],
    },
    "lab.power.pin_w": {
        "lab_metric_id": "lab.power.pin_w",
        "physical_metric_id": "pin",
        "physical_test_id": "EVT-PWR-004",
        "unit": "W",
        "golden_journeys": ["GOLDEN-08", "GOLDEN-01"],
    },
    "lab.thermal.skin_c": {
        "lab_metric_id": "lab.thermal.skin_c",
        "physical_metric_id": "skin_temp",
        "physical_test_id": "EVT-THERM-001",
        "unit": "C",
        "golden_journeys": ["GOLDEN-01", "GOLDEN-04", "GOLDEN-06"],
    },
    "lab.game.resume_success_pct": {
        "lab_metric_id": "lab.game.resume_success_pct",
        "physical_metric_id": "resume_success_rate",
        "physical_test_id": "EVT-GAME-002",
        "unit": "pct",
        "golden_journeys": ["GOLDEN-01", "GOLDEN-05"],
    },
}


def compare_prediction_vs_measurement(
    prediction: float | int | None,
    measurement: float | int | None,
    *,
    uncertainty: float | None = None,
) -> dict[str, Any]:
    """Compute error fields without declaring calibration PASS."""
    if prediction is None or measurement is None:
        return {
            "prediction": prediction,
            "measurement": measurement,
            "error": None,
            "relative_error": None,
            "uncertainty": uncertainty,
            "comparison_status": "INCOMPLETE",
            "vf_status": "PHYSICAL_PENDING",
            "CALIBRATED_EVT0": False,
        }
    err = float(measurement) - float(prediction)
    rel = None if prediction == 0 else err / float(prediction)
    return {
        "prediction": prediction,
        "measurement": measurement,
        "error": err,
        "relative_error": rel,
        "uncertainty": uncertainty,
        "comparison_status": "COMPUTED_NOT_CALIBRATED",
        "vf_status": "PHYSICAL_PENDING",
        "CALIBRATED_EVT0": False,
    }


def link_evidence(
    *,
    virtual_run_id: str,
    physical_test_id: str,
    evidence_id: str | None,
    metric_id: str,
) -> dict[str, Any]:
    validate_physical_test_id(physical_test_id)
    return {
        "schema": "gunnchos.device_lab.evidence_linkage.v1",
        "virtual_run_id": virtual_run_id,
        "physical_test_id": physical_test_id,
        "evidence_id": evidence_id,
        "metric_id": metric_id,
        "linkage_status": "LINKED" if evidence_id else "AWAITING_PHYSICAL_EVIDENCE",
        "vf_status": "PHYSICAL_PENDING",
        "CALIBRATED_EVT0": False,
    }


def build_bridge_record(
    *,
    virtual_run_id: str,
    physical_test_id: str,
    metric_id: str,
    prediction: Any,
    measurement: Any,
    uncertainty: Any = None,
    calibration_version: str = "wp010-bridge-r0",
    evidence_id: str | None = None,
    instrument_id: str | None = None,
) -> dict[str, Any]:
    validate_physical_test_id(physical_test_id)
    cmp_ = compare_prediction_vs_measurement(
        prediction if isinstance(prediction, (int, float)) else None,
        measurement if isinstance(measurement, (int, float)) else None,
        uncertainty=uncertainty if isinstance(uncertainty, (int, float)) else None,
    )
    record = {
        "bridge_id": f"bridge:{virtual_run_id}:{physical_test_id}:{metric_id}",
        "virtual_run_id": virtual_run_id,
        "physical_test_id": physical_test_id,
        "metric_id": metric_id,
        "prediction": prediction,
        "measurement": measurement,
        "error": cmp_["error"],
        "relative_error": cmp_["relative_error"],
        "uncertainty": uncertainty,
        "calibration_version": calibration_version,
        "vf_status": "PHYSICAL_PENDING",
        "claim_boundary": "HARDWARE_PROTOTYPE_PENDING",
        "evidence_id": evidence_id,
        "instrument_id": instrument_id,
        "CALIBRATED_EVT0": False,
    }
    assert_no_calibration_token(record)
    return record
