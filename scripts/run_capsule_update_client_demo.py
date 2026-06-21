#!/usr/bin/env python3
"""Capsule update client demo — simulated staging only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firmware_compat.compatibility.capsule_update_client import stage_capsule

DEVICES = ("student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set")


def main() -> int:
    manifest = ROOT / "firmware_compat/imported_hardware_contracts/capsule_update/sample_capsule_manifest.yaml"
    results = {d: stage_capsule(d, manifest_path=manifest if manifest.exists() else None) for d in DEVICES}
    out = {
        "capsule_update_client_demo": True,
        "simulated_only": True,
        "results": results,
        "claim_boundary": "Capsule update simulation — no real firmware flashed",
    }
    dest = ROOT / "results/capsule_update_client_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
