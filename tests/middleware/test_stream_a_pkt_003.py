"""STREAM-A-PKT-003 unit tests — recovery, diagnostics redaction, distinct builds."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.a_pkt003.diagnostics_collect import collect_diagnostics
from gunnchos_device_os.a_pkt003.gap_audit import run_gap_audit
from gunnchos_device_os.a_pkt003.multi_template_guest import (
    run_app_workflow,
    run_godot_workflow,
    run_research_workflow,
)
from gunnchos_device_os.a_pkt003.recovery_journeys import run_recovery_journeys
from gunnchos_device_os.middleware.resilience import FAULTS, run_fault_injection

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_gap_audit_writes(tmp_path, monkeypatch):
    # Write into real artifacts path is fine for CI; assert schema.
    doc = run_gap_audit(REPO_ROOT)
    assert doc["schema"].endswith("gap_audit.v1")
    assert doc["preservation"]["SILICON_EXACT_EMULATION"] is False
    assert (REPO_ROOT / "artifacts/a_pkt003/A_PKT003_GAP_AUDIT.json").exists()


def test_recovery_journeys_five():
    result = run_recovery_journeys(REPO_ROOT)
    assert result["fake_ab_boot"] is False
    assert result["bootable_ab_firmware"] is False
    assert len(result["journeys"]) == 5
    assert result["ok"] is True
    assert (REPO_ROOT / "artifacts/a_pkt003/ROLLBACK_RESULT.json").exists()


def test_distinct_build_systems(tmp_path):
    app = run_app_workflow(REPO_ROOT, tmp_path / "app")
    godot = run_godot_workflow(REPO_ROOT, tmp_path / "godot")
    research = run_research_workflow(REPO_ROOT, tmp_path / "research")
    systems = {app["build_system"], godot["build_system"], research["build_system"]}
    assert len(systems) == 3
    assert app["ok"] and godot["ok"] and research["ok"]


def test_diagnostics_redacts_probes():
    doc = collect_diagnostics(REPO_ROOT)
    assert doc["ok"] is True
    assert doc["redaction"]["leaks_found"] == []
    assert doc["token_OBSERVABILITY_DIAGNOSTIC_DIGITAL_PASS"] is True


def test_middleware_ten_fault_preserved():
    report = run_fault_injection()
    assert report["ok"] is True
    assert report["pass_count"] == len(FAULTS) == 10
    assert report["SILICON_EXACT_EMULATION"] is False
