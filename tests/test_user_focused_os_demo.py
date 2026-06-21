"""Tests for user-focused OS demo output."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_output_exists():
    path = ROOT / "results/user_focused_os_demo_output.json"
    assert path.exists(), "Run scripts/run_user_focused_os_demo.py first"
    data = json.loads(path.read_text())
    assert data.get("user_focused_os_alpha") is True
    assert len(data.get("scenarios", [])) >= 11
