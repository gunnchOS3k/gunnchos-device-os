"""Tests for user-focused OS demo output."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = ROOT / "scripts/run_user_focused_os_demo.py"
OUTPUT_PATH = ROOT / "results/user_focused_os_demo_output.json"

REQUIRED_SCENARIOS = {
    "pre_k_scooter",
    "high_school_car",
    "writer_studio",
    "musician_studio",
    "artist_art_table",
    "gamer_arcade",
    "cs_workshop",
    "researcher_laboratory_spaceship",
    "guardian_controls",
    "offline_library",
    "accessibility_first",
}


def _run_demo() -> None:
    result = subprocess.run(
        [sys.executable, str(DEMO_SCRIPT)],
        cwd=ROOT,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Demo script failed: {result.stderr}"


def _load_demo() -> dict:
    if not OUTPUT_PATH.exists():
        _run_demo()
    assert OUTPUT_PATH.exists(), "Demo output was not generated"
    return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))


def test_demo_output_exists_and_valid():
    data = _load_demo()
    assert data.get("user_focused_os_alpha") is True
    assert len(data.get("scenarios", [])) >= 11


def test_required_scenario_names():
    data = _load_demo()
    names = set()
    for item in data.get("scenarios", []):
        if isinstance(item, dict) and "scenario" in item:
            names.add(item["scenario"])
    missing = REQUIRED_SCENARIOS - names
    assert not missing, f"Missing scenarios: {sorted(missing)}"


def test_scenario_structure():
    data = _load_demo()
    profile_scenarios = [s for s in data.get("scenarios", []) if "profile" in s]
    assert len(profile_scenarios) >= 10
    for scenario in profile_scenarios:
        profile = scenario.get("profile", {})
        assert profile.get("persona"), f"{scenario.get('scenario')} missing persona"
        preset = scenario.get("journey_preset") or {}
        assert preset.get("id") or profile.get("journey_preset"), (
            f"{scenario.get('scenario')} missing preset"
        )
        assert scenario.get("workspace") or scenario.get("recommendations"), (
            f"{scenario.get('scenario')} missing workspace/recommendations"
        )
        rec = scenario.get("recommendations", {})
        assert "accessibility_settings" in rec or "journey_preset" in scenario
        safety = rec.get("safety_settings", {})
        assert "privacy_level" in safety or profile.get("privacy_level") is not None
