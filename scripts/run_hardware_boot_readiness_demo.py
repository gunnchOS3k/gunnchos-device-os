#!/usr/bin/env python3
"""Hardware boot readiness demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.hardware_boot_readiness import evaluate_boot_readiness
from gunnchos_device_os.hardware_manifest_loader import list_device_ids


def main() -> int:
    out = {
        "boot_readiness_demo": True,
        "devices": {d: evaluate_boot_readiness(d) for d in list_device_ids()},
        "claim_boundary": "Simulated boot readiness exists. Real hardware boot is not yet proven.",
    }
    dest = ROOT / "results/hardware_boot_readiness_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
