"""Streaming certification readiness package tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "streaming_certification" / "SERVICE_CERTIFICATION_TRACKER.yaml"
VALIDATOR = ROOT / "scripts" / "validate_streaming_certification_tracker.py"


def test_streaming_certification_docs_exist():
    for name in (
        "STREAMING_COMPATIBILITY_MATRIX.md",
        "CDM_READINESS_CHECKLIST.md",
        "HDCP_EXTERNAL_DISPLAY_CHECKLIST.md",
        "SERVICE_CERTIFICATION_TRACKER.yaml",
    ):
        assert (ROOT / "streaming_certification" / name).exists()


def test_phase4e_doc_exists():
    assert (ROOT / "docs" / "PHASE4E_STREAMING_CDM_CERTIFICATION.md").exists()


def test_validate_streaming_certification_tracker_passes():
    rc = subprocess.call(["python3", str(VALIDATOR)], cwd=ROOT)
    assert rc == 0


def test_no_service_certified_without_evidence_path():
    data = yaml.safe_load(TRACKER.read_text(encoding="utf-8"))
    for service_id, entry in data["services"].items():
        if entry.get("certification_status") == "certified":
            evidence = entry.get("evidence_path")
            assert evidence, f"{service_id} is certified but has no evidence_path"
            assert (ROOT / evidence).exists(), f"{service_id} evidence missing: {evidence}"


def test_local_media_separate_from_drm_streaming():
    data = yaml.safe_load(TRACKER.read_text(encoding="utf-8"))
    local = data["services"]["local_media"]
    assert local["drm_cdm_required"] is False
    assert "not drm" in local["claim_boundary"].lower() or "non-drm" in local["claim_boundary"].lower()


def test_no_drm_circumvention_language_in_tracker():
    text = TRACKER.read_text(encoding="utf-8").lower()
    assert "bypass drm" not in text
    assert "crack widevine" not in text
    assert "strip hdcp" not in text
