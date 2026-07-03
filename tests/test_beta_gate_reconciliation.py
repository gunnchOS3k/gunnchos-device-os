"""Beta gate reconciliation tests (Phase 4H)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "beta_gate" / "beta_gate_status.yaml"


@pytest.fixture(scope="module")
def gate_data() -> dict:
    return yaml.safe_load(STATUS.read_text(encoding="utf-8"))


def test_beta_ready_is_false(gate_data: dict):
    assert gate_data["beta_ready"] is False


def test_phase4_merged_items_implemented(gate_data: dict):
    items = gate_data["items"]
    for item_id in (
        "encrypted_storage",
        "foot_racing_playable",
        "earth_species_playable",
        "streaming_certification",
        "legal_privacy_accessibility",
        "hardware_evidence",
        "bootable_image",
    ):
        assert items[item_id]["status"] in ("prototype", "implemented"), item_id


def test_secure_boot_mdm_still_missing_or_prototype(gate_data: dict):
    items = gate_data["items"]
    assert items["secure_boot"]["status"] in ("missing", "prototype")
    assert items["production_mdm"]["status"] in ("missing", "prototype")
    assert items["secure_boot"]["status"] != "validated"
    assert items["production_mdm"]["status"] != "validated"


def test_remaining_blockers_list(gate_data: dict):
    blockers = gate_data.get("remaining_blockers", [])
    assert len(blockers) >= 7
    ids = {b["id"] for b in blockers}
    assert "production_filesystem" in ids
    assert "physical_hardware" in ids
    assert "bootable_os" in ids
    assert "streaming_cdm" in ids
    assert "secure_boot" in ids


def test_validate_beta_gate_script_passes():
    rc = subprocess.call(["python3", str(ROOT / "scripts" / "validate_beta_gate.py")], cwd=ROOT)
    assert rc == 0


def test_cannot_set_validated_without_evidence(gate_data: dict):
    items = gate_data["items"]
    for item_id in (
        "hardware_evidence",
        "bootable_image",
        "streaming_certification",
        "secure_boot",
        "production_mdm",
        "legal_privacy_accessibility",
        "encrypted_storage",
    ):
        assert items[item_id]["status"] != "validated", item_id


def test_beta_candidate_report_exists():
    report = ROOT / "release_artifacts" / "BETA_CANDIDATE_REPORT.md"
    text = report.read_text(encoding="utf-8")
    assert "not allowed yet" in text.lower()
    assert "beta_ready" in text.lower() or "false" in text
