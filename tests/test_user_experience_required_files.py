"""Tests that required user experience files exist."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "product/USER_FOCUSED_OS_PRD.md",
    "config/personas.yaml",
    "config/journey_presets.yaml",
    "gunnchos_device_os/customization_engine.py",
    "scripts/validate_user_focused_os.py",
]


def test_required_files():
    for rel in REQUIRED:
        assert (ROOT / rel).exists(), f"Missing {rel}"
