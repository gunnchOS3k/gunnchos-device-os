"""Tests for update/recovery digital completeness."""
from __future__ import annotations

from gunnchos_device_os.update_recovery_completeness import (
    TOKEN_UPDATE_RECOVERY_PASS,
    InterruptPoint,
    UpdateRecoverySuite,
    run_update_recovery_completeness,
)


def test_update_recovery_suite_pass():
    report = run_update_recovery_completeness()
    assert report["ok"] is True
    assert report["token"] == TOKEN_UPDATE_RECOVERY_PASS
    assert report["production_keys_used"] is False
    assert report["ab_strategy"].startswith("A/B")
    names = {s["scenario"] for s in report["scenarios"]}
    assert "corrupt_download_recovers" in names
    assert "rollback_after_bad_health" in names
    assert "factory_reset" in names
    assert any(n.startswith("interrupted_") for n in names)


def test_interrupted_points_cover_pipeline():
    suite = UpdateRecoverySuite()
    for point in InterruptPoint:
        row = suite.scenario_interrupted_update(point)
        assert row["ok"] is True, point
