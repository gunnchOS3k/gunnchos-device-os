"""IMT-2030 / Rel-20/21 migration harness — tracking only, no compliance."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.connectivity.imt2030_migration import (
    FORBIDDEN_CLAIMS,
    Imt2030MigrationHarness,
)
from gunnchos_device_os.phase_xv.ntn_migration import NtnMigrationHarness, STANDARDS_REGISTER


def test_imt2030_harness_tracks_rel20_rel21_without_compliance(tmp_path: Path):
    report = Imt2030MigrationHarness(tmp_path).evaluate()
    assert report["ok"] is True
    assert report["STANDARDIZED_6G"] is False
    assert report["CARRIER_ACCEPTED"] is False
    assert report["rel20"]["id"] == "3GPP-Rel-20"
    assert report["rel21"]["status"] == "TRACKER_ONLY"
    assert report["rm520n_ntn_claimed"] is False
    assert report["rm520n_6g_claimed"] is False
    assert "6G certified" in FORBIDDEN_CLAIMS
    assert (tmp_path / "IMT2030_MIGRATION.json").is_file()
    scenarios = report["usage_scenarios"]
    assert "ubiquitous_connectivity" in scenarios
    assert all(s["STANDARDIZED_6G"] is False for s in scenarios.values())


def test_ntn_migration_register_includes_rel20_rel21(tmp_path: Path):
    ids = {e["id"] for e in STANDARDS_REGISTER}
    assert "3GPP-Rel-20" in ids
    assert "3GPP-Rel-21" in ids
    result = NtnMigrationHarness(tmp_path).e2e()
    assert result["ok"] is True
    assert result["STANDARDIZED_6G"] is False
    assert result["CARRIER_ACCEPTED"] is False
    assert result["rm520n_ntn_claimed"] is False
    rel21 = next(e for e in STANDARDS_REGISTER if e["id"] == "3GPP-Rel-21")
    assert rel21["status"] == "TRACKER_ONLY"
