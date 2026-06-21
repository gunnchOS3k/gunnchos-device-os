#!/usr/bin/env python3
"""Validate hardware device profile manifests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.hardware_manifest_loader import list_device_ids, validate_profile

REQUIRED = {"student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set"}
REQUIRED_SECTIONS = ("display", "input", "network", "storage", "memory", "battery", "thermal", "accessibility")


def main() -> int:
    errors: list[str] = []
    ids = set(list_device_ids())
    if not REQUIRED.issubset(ids):
        errors.append(f"Missing device profiles: {sorted(REQUIRED - ids)}")

    for did in list_device_ids():
        errors.extend(f"{did}: {e}" for e in validate_profile(did))
        import yaml
        data = yaml.safe_load((ROOT / f"hardware_compat/device_profiles/{did}.yaml").read_text())
        for sec in REQUIRED_SECTIONS:
            if sec not in data:
                errors.append(f"{did} missing section {sec}")

    if errors:
        print("VALIDATE_HARDWARE_MANIFESTS FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"validate_hardware_manifests: OK ({len(ids)} profiles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
