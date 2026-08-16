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


def test_rings_inject_anti_replay_and_stale():
    from gunnchos_device_os.device_lab.hw_backends.rings import RingsBackend

    rings = RingsBackend()
    rings.start(evidence_dir=REPO_ROOT / "artifacts" / "a_pkt003" / "_ring_test", repo_root=REPO_ROOT)
    first = rings.inject(target="browser", confidence=0.95, gesture="click", nonce="pkt003-n1")
    assert first["delivered"] is True
    replay = rings.inject(target="browser", confidence=0.95, gesture="click", nonce="pkt003-n1")
    assert replay["delivered"] is False
    assert replay["reject"]["reason"] == "replay"
    stale = rings.inject(target="browser", confidence=0.95, gesture="click", stale=True, nonce="pkt003-stale")
    assert stale["delivered"] is False
    assert stale["reject"]["reason"] == "stale"
    wrong = rings.inject(wrong_target=True, confidence=0.95, target="browser")
    assert wrong["delivered"] is False
    assert wrong["reject"]["reason"] == "wrong_target"


def test_evidence_scrub_redacts_host_paths():
    from gunnchos_device_os.a_pkt003.evidence_scrub import scrub_obj

    sample = {
        "bundle_dir": str(REPO_ROOT / "artifacts/a_pkt003/continuity/x"),
        "playwright_error": "Executable doesn't exist at /var/folders/dp/abc/T/playwright/chrome",
        "host": "Edmunds-MacBook-Pro.local",
        "nested": {"dest": "/Users/gunnchos/Downloads/foo/artifacts/a_pkt003/y.json"},
    }
    cleaned = scrub_obj(sample, REPO_ROOT)
    blob = str(cleaned)
    assert "/Users/gunnchos" not in blob
    assert "/var/folders/" not in blob
    assert cleaned["host"] == "<lab-host>"
    assert "Edmunds-MacBook" not in blob
