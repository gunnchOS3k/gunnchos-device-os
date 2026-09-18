"""CX2C — authentic journeys + evidence artifacts."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx1 import FULL_COMPLETE_EXPERIENCE_COMPLETE as CX1_COMPLETE
from gunnchos_device_os.cx2 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2.evidence import write_evidence
from gunnchos_device_os.cx2.journeys import AuthenticJourneyRunner
from gunnchos_device_os.cx2.shell.product_shell import ProductShell


def test_journeys_j1_j7_honest(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    results = AuthenticJourneyRunner(shell).run_all()
    assert set(results) == {"J1", "J2", "J3", "J4", "J5", "J6", "J7"}
    for key, result in results.items():
        assert "evidence_class" in result
        # Never inflate to REAL_USER_JOURNEY_DIGITAL_PASS without GUI window + provider
        if result["evidence_class"] == "REAL_USER_JOURNEY_DIGITAL_PASS":
            assert result.get("ok") is True
    assert results["J6"]["HUMAN_A11Y_PENDING"] is True
    assert results["J1"]["PHYSICAL_PRINTER_VALIDATION_PENDING"] is True
    assert results["J3"]["ok"] is True
    assert results["J4"]["ok"] is True
    assert results["J5"]["ok"] is True
    assert results["J7"]["ok"] is True


def test_evidence_writer(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    report = write_evidence(repo, tmp_path / "home")
    assert report["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert CX1_COMPLETE is False
    root = repo / "artifacts" / "complete_experience" / "cx2"
    assert (root / "CX2_EVIDENCE_REPORT.json").exists()
    assert (root / "CX1_RECLASSIFICATION.json").exists()
    assert (root / "JOURNEYS.json").exists()
    assert (root / "HUMAN_A11Y_VALIDATION_PACKET.md").exists()
