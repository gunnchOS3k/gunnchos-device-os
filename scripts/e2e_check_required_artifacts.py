#!/usr/bin/env python3
from pathlib import Path
import sys

DEVICES = ["student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set"]
CAMPUSES = ["gary", "ghana", "guyana", "gaza", "geelong", "graham_land", "germany"]
ROOT = Path(__file__).resolve().parents[1]

REQ = [
    "docs/00_START_HERE.md",
    "REQUIREMENTS.md",
    "results/e2e/device_os_e2e_report.md",
    "results/sbom/gunnchos_device_os.spdx.json",
    "results/sbom/gunnchos_device_os.cyclonedx.json",
    "results/update_system/sample_update_manifest.json",
    "shared_contracts/hardware_os_device_profile.schema.json",
    "src/gunnchos_core/config_loader.py",
    "src/mode_manager/modes.py",
]

for d in DEVICES:
    REQ += [
        f"configs/devices/{d}.yaml",
        f"results/device_states/{d}_state.json",
    ]

for site in CAMPUSES:
    REQ += [f"results/campus_device_modes/{site}_mode_report.md"]


def main() -> int:
    missing = [p for p in REQ if not (ROOT / p).exists()]
    if missing:
        print("FAIL", missing)
        return 1
    print("PASS device-os e2e artifacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
