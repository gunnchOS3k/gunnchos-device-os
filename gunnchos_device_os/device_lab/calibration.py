"""Future calibration contract schemas — no calibration tokens before EVT."""
from __future__ import annotations

from typing import Any


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


def calibration_status() -> dict[str, Any]:
    return {
        **CALIBRATION_CONTRACT_SCHEMA,
        "CALIBRATED_EVT0": False,
        "status": "PHYSICAL_PENDING",
        "note": "No calibration token may be set before real EVT measurements.",
    }


def assert_no_calibration_token(payload: dict[str, Any]) -> None:
    forbidden = {"CALIBRATED_EVT0", "CALIBRATED_TARGET", "PHYSICAL_CORRELATION_PASS"}
    for k in forbidden:
        if payload.get(k) in (True, "PASS", "CALIBRATED"):
            raise AssertionError(f"calibration token {k} forbidden without EVT")
