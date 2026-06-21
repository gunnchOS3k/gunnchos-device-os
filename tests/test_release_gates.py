"""Tests for release gates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_gates():
    for name in ("ALPHA_GATE", "BETA_GATE", "RELEASE_CANDIDATE_GATE", "GA_RELEASE_GATE"):
        assert (ROOT / f"release_gates/{name}.md").exists()
    matrix = (ROOT / "release_gates/RELEASE_GATE_MATRIX.md").read_text(encoding="utf-8")
    assert "alpha" in matrix.lower()
    assert "not" in matrix.lower() or "not_started" in matrix.lower()
