"""Tests for WAIKE integration configs."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_tutor_cards():
    data = yaml.safe_load((ROOT / "config/waike_tutor_cards.yaml").read_text())
    cards = data["tutor_cards"]
    assert len(cards) >= 6
    for cid, card in cards.items():
        for field in ("card_id", "audience", "mode", "prompt", "student_task", "offline_option"):
            assert field in card, f"{cid} missing {field}"


def test_student_tasks():
    data = yaml.safe_load((ROOT / "config/waike_student_tasks.yaml").read_text())
    tasks = data["student_tasks"]
    assert "prek_safe_task" in tasks
    assert "research_measurement_task" in tasks
    assert data["mode_pathways"]["Offline"] == "low_bandwidth_access"
