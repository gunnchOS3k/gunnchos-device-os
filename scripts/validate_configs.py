#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
DEVICES = ["student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set"]
REQUIRED_KEYS = ["device_id", "supported_modes", "default_mode"]


def main() -> int:
    missing = []
    for d in DEVICES:
        p = ROOT / "configs/devices" / f"{d}.yaml"
        if not p.exists():
            missing.append(str(p))
            continue
        if yaml:
            data = yaml.safe_load(p.read_text())
            for k in REQUIRED_KEYS:
                if k not in data:
                    missing.append(f"{p}:{k}")
    if missing:
        print("FAIL validate-configs", missing)
        return 1
    print("PASS validate-configs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
