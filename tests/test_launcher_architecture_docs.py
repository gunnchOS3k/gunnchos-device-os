"""Tests launcher architecture docs exist."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "docs/LAUNCHER_MOCK_ARCHITECTURE.md",
    "docs/LAUNCHER_COMPONENT_MAP.md",
    "apps/launcher_mock/README.md",
    "apps/launcher_mock/src/user-focused/README.md",
]


def test_launcher_docs():
    for rel in DOCS:
        assert (ROOT / rel).exists(), rel
