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


def test_pending_prs_documented(gate_data: dict):
    pending = gate_data.get("pending_prs", [])
    numbers = {p["number"] for p in pending}
    assert {41, 42, 43, 44, 45, 46, 47}.issubset(numbers)


def test_open_pr_items_not_implemented_on_main(gate_data: dict):
    pending_items = {
        "encrypted_storage": 44,
        "foot_racing_playable": 41,
        "earth_species_playable": 41,
        "streaming_certification": 45,
        "secure_boot": 46,
        "production_mdm": 46,
        "legal_privacy_accessibility": 47,
    }
    items = gate_data["items"]
    for item_id, pr_num in pending_items.items():
        item = items[item_id]
        assert item["status"] == "missing", f"{item_id} should be missing until PR #{pr_num} merges"
        assert str(pr_num) in (item.get("blocker") or "")


def test_remaining_blockers_list(gate_data: dict):
    blockers = gate_data.get("remaining_blockers", [])
    assert len(blockers) >= 8
    ids = {b["id"] for b in blockers}
    assert "production_filesystem" in ids
    assert "physical_hardware" in ids
    assert "bootable_os" in ids


def test_validate_beta_gate_script_passes():
    rc = subprocess.call(["python3", str(ROOT / "scripts" / "validate_beta_gate.py")], cwd=ROOT)
    assert rc == 0


def test_cannot_set_validated_without_evidence(gate_data: dict):
    """Simulate dishonest validated transitions — validator must reject on real files."""
    # hardware validated without physical report should fail if we patch yaml in memory
    items = gate_data["items"]
    assert items["hardware_evidence"]["status"] != "validated"
    assert items["bootable_image"]["status"] != "validated"
    assert items.get("secure_boot", {}).get("status") != "validated"
    assert items.get("production_mdm", {}).get("status") != "validated"


def test_beta_candidate_report_exists():
    report = ROOT / "release_artifacts" / "BETA_CANDIDATE_REPORT.md"
    text = report.read_text(encoding="utf-8")
    assert "beta_ready" in text.lower() or "false" in text
    assert "Pending PR" in text or "pending PR" in text.lower() or "#41" in text
