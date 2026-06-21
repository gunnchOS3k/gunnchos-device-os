#!/usr/bin/env python3
"""Firmware probe demo — runs host probe for all SKUs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firmware_compat.probes.firmware_probe import run_probes

DEVICES = ("student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set")


def main() -> int:
    results = {}
    for device in DEVICES:
        fixture = ROOT / f"firmware_compat/fixtures/sample_host_probe_{device}.json"
        results[device] = run_probes(device, fixture_path=fixture if fixture.exists() else None)

    out = {
        "firmware_probe_demo": True,
        "device_count": len(results),
        "results": results,
        "claim_boundary": "Host/emulated firmware probe demo — physical-board validation pending",
    }
    dest = ROOT / "results/firmware_probe_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
