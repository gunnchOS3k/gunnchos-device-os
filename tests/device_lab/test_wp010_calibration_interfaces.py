"""WP-010 Device Lab calibration interfaces — schema readiness, no VF4 promotion."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab.calibration import (
    assert_no_calibration_token,
    build_bridge_record,
    calibration_status,
    compare_prediction_vs_measurement,
    ingest_calibration_record,
    link_evidence,
    map_metric,
    validate_physical_test_id,
)
from gunnchos_device_os.device_lab.instrument_import import import_instrument_payload, list_adapters


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "gunnchos_device_os" / "device_lab" / "schemas"


def test_physical_test_id_schema_and_validator():
    validate_physical_test_id("EVT-DOCK-001")
    with pytest.raises(ValueError):
        validate_physical_test_id("DOCK-1")
    schema = json.loads((SCHEMA_DIR / "physical_test_id.schema.json").read_text())
    assert schema["pattern"].startswith("^EVT-")


def test_ingestion_rejects_calibration_token_and_keeps_vf4_pending():
    with pytest.raises(AssertionError):
        ingest_calibration_record(
            {
                "virtual_run_id": "vr1",
                "physical_test_id": "EVT-AI-001",
                "metric_id": "ttft",
                "prediction": 100,
                "measurement": 120,
                "calibration_version": "r0",
                "CALIBRATED_EVT0": True,
            }
        )
    rec = ingest_calibration_record(
        {
            "virtual_run_id": "vr1",
            "physical_test_id": "EVT-AI-001",
            "metric_id": "ttft",
            "prediction": 100,
            "measurement": None,
            "calibration_version": "r0",
        }
    )
    assert rec["vf_status"] == "PHYSICAL_PENDING"
    assert rec["CALIBRATED_EVT0"] is False


def test_metric_mapping_and_comparison():
    row = map_metric("lab.ai.ttft_ms")
    assert row["physical_test_id"] == "EVT-AI-001"
    cmp_ = compare_prediction_vs_measurement(100, 120, uncertainty=5)
    assert cmp_["error"] == 20
    assert cmp_["vf_status"] == "PHYSICAL_PENDING"
    assert cmp_["CALIBRATED_EVT0"] is False
    assert cmp_["comparison_status"] == "COMPUTED_NOT_CALIBRATED"


def test_evidence_linkage_and_bridge():
    link = link_evidence(
        virtual_run_id="vr1",
        physical_test_id="EVT-RING-003",
        evidence_id=None,
        metric_id="pose_error",
    )
    assert link["linkage_status"] == "AWAITING_PHYSICAL_EVIDENCE"
    bridge = build_bridge_record(
        virtual_run_id="vr1",
        physical_test_id="EVT-DOCK-001",
        metric_id="pd_contract",
        prediction=60,
        measurement=None,
    )
    assert bridge["vf_status"] == "PHYSICAL_PENDING"
    assert_no_calibration_token(bridge)


def test_instrument_adapters():
    assert "usb_pd_analyzer_json" in list_adapters()
    pd = import_instrument_payload(
        "usb_pd_analyzer_json",
        {"instrument_id": "INST-USB-PD", "contract_w": 65, "instrument_serial": "X"},
    )
    assert pd["measurement"] == 65
    assert pd["vf_status"] == "PHYSICAL_PENDING"
    csv_payload = "channel,temp_c\nskin,38.5\nsoc,62.0\n"
    th = import_instrument_payload("thermocouple_logger_csv", csv_payload)
    assert th["measurement"] == 38.5
    assert th["CALIBRATED_EVT0"] is False


def test_status_honesty():
    st = calibration_status()
    assert st["status"] == "PHYSICAL_PENDING"
    assert st["VF4"] == "PHYSICAL_PENDING"
    assert st["CALIBRATED_EVT0"] is False
    art = json.loads(
        (ROOT / "artifacts/wp010_lab_calibration/LAB_CALIBRATION_INTERFACE_READINESS.json").read_text()
    )
    assert art["VF4"] == "PHYSICAL_PENDING"
    assert art["CALIBRATED_EVT0"] is False
    assert art["LAB_FUTURE_007_executed"] is False


def test_required_schemas_present():
    for name in [
        "physical_test_id.schema.json",
        "calibration_ingestion.schema.json",
        "metric_mapping.schema.json",
        "prediction_vs_measurement.schema.json",
        "evidence_linkage.schema.json",
        "calibration_bridge.schema.json",
    ]:
        assert (SCHEMA_DIR / name).is_file(), name
