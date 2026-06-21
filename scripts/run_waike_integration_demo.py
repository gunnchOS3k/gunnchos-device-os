#!/usr/bin/env python3
"""WAIKE integration demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.waike_integration import deploy_lesson, list_offline_lessons


def _load_cards():
    return yaml.safe_load((ROOT / "config/waike_tutor_cards.yaml").read_text())["tutor_cards"]


def _load_tasks():
    return yaml.safe_load((ROOT / "config/waike_student_tasks.yaml").read_text())


def main() -> int:
    cards = _load_cards()
    tasks = _load_tasks()
    out = {
        "tutor_cards": list(cards.keys()),
        "sample_card": cards["school_wireless_basics"],
        "student_tasks": list(tasks["student_tasks"].keys()),
        "mode_pathways": tasks["mode_pathways"],
        "offline_lessons": list_offline_lessons(),
        "deploy": deploy_lesson("python_starter_pack", "student"),
        "claim_boundary": "WAIKE integration alpha — tutor cards and tasks are config-driven",
        "mock": True,
    }
    dest = ROOT / "results/waike_integration_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
