"""Product-quality tests for clean installation (CG-QUALITY-001)."""
from __future__ import annotations

from gunnchos_device_os.clean_installation import (
    TOKEN_CLEAN_INSTALLATION_PASS,
    CleanInstallationSuite,
    run_clean_installation,
)


def test_product_quality_clean_installation_pass():
    report = run_clean_installation()
    assert report["ok"] is True
    assert report["token"] == TOKEN_CLEAN_INSTALLATION_PASS
    assert report["requirement_id"] == "CG-QUALITY-001"
    assert report["shipping_installer_claimed"] is False
    assert report["hardware_validated"] is False


def test_product_quality_clean_installation_rejects_dirty_target():
    suite = CleanInstallationSuite()
    dirty = suite.scenario_dirty_target_fails()
    assert dirty.ok is False
    assert "profiles" in dirty.residual_keys


def test_product_quality_clean_installation_wiped_target_ok():
    suite = CleanInstallationSuite()
    clean = suite.scenario_wiped_target_passes()
    assert clean.ok is True
    assert clean.checks["no_prior_user_profile"] is True
