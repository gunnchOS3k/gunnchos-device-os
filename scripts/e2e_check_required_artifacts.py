#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQ = [
    "docs/00_START_HERE.md",
    "docs/6G_URLLC_REQUIREMENTS_MATRIX.md",
    "docs/video_walkthrough_script.md",
    "results/e2e/device_os_e2e_report.md",
    "results/e2e/seven_gc_device_export.json",
    "src/gunnchos_launcher/mode_manager.py",
    "src/gunnchos_launcher/seven_gc_bridge.py",
]

def main():
    missing = [p for p in REQ if not (ROOT / p).exists()]
    if missing:
        print("FAIL", missing)
        return 1
    print("PASS device-os e2e artifacts")
    return 0

if __name__ == "__main__":
    sys.exit(main())
