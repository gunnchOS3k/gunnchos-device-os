#!/usr/bin/env python3
"""Device-specific mode demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.hardware_compatibility_engine import evaluate_compatibility
from gunnchos_device_os.hardware_manifest_loader import list_device_ids


DEVICE_MODES = {
    "student_14_5": ["School", "Developer", "Studio", "Workshop", "Laboratory"],
    "handheld_hybrid": ["Arcade", "Play", "Media", "Offline"],
    "ds_xl_coder": ["Coder", "Workshop", "Developer"],
    "wearables_arena_set": ["Play", "School", "Developer"],
}


def main() -> int:
    results = []
    for device_id in list_device_ids():
        for mode in DEVICE_MODES.get(device_id, []):
            r = evaluate_compatibility(device_id, mode=mode)
            results.append({
                "device_id": device_id,
                "mode": mode,
                "compatible": r.compatible,
                "status": r.status,
                "user_message": r.user_message,
                "technical_log": r.technical_log,
                "fallback": r.recommended_fallbacks,
            })
    out = {
        "device_specific_mode_demo": True,
        "results": results,
        "claim_boundary": "Simulated device-mode matrix — requires real hardware validation",
    }
    dest = ROOT / "results/device_specific_mode_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
