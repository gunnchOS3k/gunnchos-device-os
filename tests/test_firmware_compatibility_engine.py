"""Tests for firmware compatibility engine."""
from __future__ import annotations

from pathlib import Path

from firmware_compat.compatibility.firmware_compatibility_engine import evaluate_firmware_compatibility
from firmware_compat.probes.firmware_probe import run_probes

ROOT = Path(__file__).resolve().parents[1]


def _probe(device: str) -> dict:
    fixture = ROOT / f"firmware_compat/fixtures/sample_host_probe_{device}.json"
    return run_probes(device, fixture_path=fixture)


def test_student_school_compatible():
    r = evaluate_firmware_compatibility("student_14_5", _probe("student_14_5"), mode="School")
    assert r["compatible"]
    assert r["status"] in ("pass", "warn")
    assert "physical_board_validation_pending" in r["evidence_required"]


def test_wearables_rejects_developer():
    r = evaluate_firmware_compatibility("wearables_arena_set", _probe("wearables_arena_set"), mode="Developer")
    assert not r["compatible"]
    assert r["status"] == "fail"
    assert r["fallbacks"]


def test_research_requires_consent():
    r = evaluate_firmware_compatibility(
        "student_14_5", _probe("student_14_5"), mode="Research Measurement", consent=False
    )
    assert not r["compatible"]
