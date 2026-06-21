#!/usr/bin/env python3
"""Firmware compatibility demo — engine scenarios across SKUs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firmware_compat.compatibility.firmware_compatibility_engine import evaluate_firmware_compatibility
from firmware_compat.probes.firmware_probe import run_probes


def _eval(device: str, *, mode: str = "", fixture: bool = True, **kw) -> dict:
    fixture_path = ROOT / f"firmware_compat/fixtures/sample_host_probe_{device}.json" if fixture else None
    probe = run_probes(device, fixture_path=fixture_path)
    result = evaluate_firmware_compatibility(device, probe, mode=mode, **kw)
    result["scenario_mode"] = mode
    return result


def main() -> int:
    scenarios = [
        {"name": "student_school", "result": _eval("student_14_5", mode="School")},
        {"name": "student_research_no_consent", "result": _eval("student_14_5", mode="Research Measurement", consent=False)},
        {"name": "student_research_with_consent", "result": _eval("student_14_5", mode="Research Measurement", consent=True)},
        {"name": "handheld_play", "result": _eval("handheld_hybrid", mode="Play")},
        {"name": "ds_xl_coder_workshop", "result": _eval("ds_xl_coder", mode="Workshop")},
        {"name": "wearables_play_marshal", "result": _eval("wearables_arena_set", mode="Play", marshal_control=True)},
        {"name": "wearables_developer_blocked", "result": _eval("wearables_arena_set", mode="Developer")},
        {"name": "student_dock_missing", "result": _eval("student_14_5", mode="School", dock_attached=False)},
    ]
    out = {
        "firmware_compatibility_demo": True,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "claim_boundary": "Firmware compatibility harness demo — physical-board validation pending",
    }
    dest = ROOT / "results/firmware_compatibility_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
