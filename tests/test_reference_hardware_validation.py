"""Reference hardware validation package tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "hardware_validation" / "reference_device_matrix.yaml"
TEMPLATE = ROOT / "hardware_validation" / "reference_device_report.template.md"
EXAMPLE = ROOT / "hardware_validation" / "reference_device_report.example.md"
COLLECTOR = ROOT / "scripts" / "collect_reference_hardware_info.py"
VALIDATOR = ROOT / "scripts" / "validate_hardware_report.py"
PHASE_DOC = ROOT / "docs" / "PHASE4C_HARDWARE_VALIDATION.md"
BOUNDARY = ROOT / "hardware_validation" / "HARDWARE_CLAIM_BOUNDARY.md"


def test_phase4c_files_exist():
    for path in (MATRIX, TEMPLATE, EXAMPLE, COLLECTOR, VALIDATOR, PHASE_DOC, BOUNDARY):
        assert path.exists(), f"Missing Phase 4C artifact: {path}"


def test_reference_device_matrix_structure():
    data = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    area_ids = {a["id"] for a in data["validation_areas"]}
    assert "cpu_architecture" in area_ids
    assert "launcher_startup" in area_ids
    assert set(data["area_defaults"].keys()) == area_ids
    assert data["container_reference"]["validation_status"] == "container_only"
    for device in data["reference_devices"].values():
        assert device["validation_status"] != "validated"


def test_example_report_is_container_only():
    text = EXAMPLE.read_text(encoding="utf-8").lower()
    assert "container only" in text or "container-only" in text
    assert "physical_validation_performed: false" in text
    assert "container_only: true" in text
    assert "does not claim physical" in text


def test_collector_runs_safely(tmp_path):
    out = tmp_path / "snapshot.json"
    rc = subprocess.call(
        ["python3", str(COLLECTOR), "--output", str(out)],
        cwd=ROOT,
    )
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "memory_gb_rounded" in data
    assert "root_disk_gb_rounded" in data
    assert "network_interfaces" in data
    payload = json.dumps(data).lower()
    for forbidden in ("serial_number", "mac_address", "hostname", "uuid"):
        assert forbidden not in payload


def test_collector_validate_only(tmp_path):
    out = tmp_path / "snapshot.json"
    subprocess.check_call(["python3", str(COLLECTOR), "--output", str(out)], cwd=ROOT)
    rc = subprocess.call(
        ["python3", str(COLLECTOR), "--validate-only", str(out)],
        cwd=ROOT,
    )
    assert rc == 0


def test_validate_hardware_report_script_passes():
    rc = subprocess.call(["python3", str(VALIDATOR)], cwd=ROOT)
    assert rc == 0


def test_beta_gate_rejects_validated_hardware_without_physical_report():
    """hardware_evidence must stay prototype until a real physical report exists."""
    status = yaml.safe_load((ROOT / "beta_gate" / "beta_gate_status.yaml").read_text(encoding="utf-8"))
    hw = status["items"]["hardware_evidence"]
    assert hw["status"] == "prototype"
    rc = subprocess.call(["python3", str(ROOT / "scripts" / "validate_beta_gate.py")], cwd=ROOT)
    assert rc == 0


def test_hardware_claim_boundary_no_false_physical_claim():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert "No physical hardware validation" in text
    assert "container_only" in text.lower() or "container-only" in text.lower()
