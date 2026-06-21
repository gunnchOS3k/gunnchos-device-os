"""Tests for hardware release evidence docs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_matrix():
    p = ROOT / "hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8").lower()
    assert "simulated" in text or "needs_real_hardware" in text
