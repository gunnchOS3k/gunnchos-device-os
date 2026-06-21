"""Tests for capsule update client."""
from __future__ import annotations

from pathlib import Path

from firmware_compat.compatibility.capsule_update_client import stage_capsule

ROOT = Path(__file__).resolve().parents[1]


def test_stage_capsule_simulated():
    manifest = ROOT / "firmware_compat/imported_hardware_contracts/capsule_update/sample_capsule_manifest.yaml"
    r = stage_capsule("student_14_5", manifest_path=manifest)
    assert r["status"] == "success"
    assert r["simulated_only"] is True
    assert r["reboot_required"] is True


def test_stage_capsule_wrong_device():
    manifest = ROOT / "firmware_compat/imported_hardware_contracts/capsule_update/sample_capsule_manifest.yaml"
    r = stage_capsule("handheld_hybrid", manifest_path=manifest)
    assert r["status"] == "fail"
