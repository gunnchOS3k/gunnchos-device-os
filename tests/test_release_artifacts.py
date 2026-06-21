"""Tests for release artifacts model."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_artifact_manifest():
    p = ROOT / "release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8").lower()
    assert "alpha" in text
    assert "release candidate" in text or "release_candidate" in text
