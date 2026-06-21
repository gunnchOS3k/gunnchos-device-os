#!/usr/bin/env python3
"""Guardian policy demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.guardian_controls import enable_guardian_controls
from gunnchos_device_os.guardian_policy import approve_app, approve_mode, get_age_band_policy


def main() -> int:
    out = {
        "elementary_policy": get_age_band_policy("elementary"),
        "app_blocked": approve_app("steam", "elementary", []),
        "app_approved": approve_app("waike_offline", "elementary", ["waike_offline"]),
        "mode_blocked": approve_mode("Developer", "elementary"),
        "mode_approved": approve_mode("Developer", "elementary", guardian_approved=True),
        "enabled": enable_guardian_controls("demo-child", "elementary"),
        "limitations": "Stub/model only — not production parental-control enforcement",
        "mock": True,
    }
    dest = ROOT / "results/guardian_policy_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
