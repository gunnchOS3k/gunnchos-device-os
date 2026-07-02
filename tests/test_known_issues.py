"""Known issues document tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN = ROOT / "docs" / "KNOWN_ISSUES.md"


def test_known_issues_exists():
    assert KNOWN.exists()


def test_known_issues_has_required_sections():
    text = KNOWN.read_text(encoding="utf-8")
    for token in ("Severity", "Workaround", "Beta impact", "Release blocker", "KI-"):
        assert token in text
