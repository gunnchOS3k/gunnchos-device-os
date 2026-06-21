"""Tests for issue closure matrix."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_closure_matrix_exists():
    p = ROOT / "docs/ISSUE_CLOSURE_MATRIX.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    for num in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12"):
        assert f"#{num}" in text
