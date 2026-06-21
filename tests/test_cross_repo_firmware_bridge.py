"""Tests for cross-repo firmware bridge."""
from __future__ import annotations

from pathlib import Path

from cross_repo_firmware_bridge.sync_firmware_contracts import sync_contracts

ROOT = Path(__file__).resolve().parents[1]


def test_sync_with_hardware_repo():
    hw = ROOT.parent / "gunnchos-hardware-industrial-design"
    report = sync_contracts(hw, allow_fallback=True)
    assert report["status"] == "ok"
    assert report["copy_count"] >= 4 or report["fallback_used"]


def test_sync_fallback_without_repo():
    report = sync_contracts(ROOT / "_missing_hw_repo", allow_fallback=True)
    assert report["status"] == "ok"
    assert report["fallback_used"] is True


def test_imported_manifests_exist():
    manifests = list((ROOT / "firmware_compat/imported_hardware_contracts/manifests").glob("*.yaml"))
    assert len(manifests) >= 4
