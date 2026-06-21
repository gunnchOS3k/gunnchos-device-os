#!/usr/bin/env python3
"""Main firmware host probe CLI — orchestrates sub-probes."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from firmware_compat.probes._host_probe_common import CLAIM, PROBE_VERSION, detect_host_os
from firmware_compat.probes import (
    acpi_probe,
    battery_probe,
    devicetree_probe,
    display_probe,
    dock_probe,
    input_probe,
    network_probe,
    storage_probe,
    thermal_probe,
    uefi_probe,
)

PROBE_MODULES = {
    "uefi": uefi_probe,
    "acpi": acpi_probe,
    "devicetree": devicetree_probe,
    "display": display_probe,
    "dock": dock_probe,
    "battery": battery_probe,
    "thermal": thermal_probe,
    "input": input_probe,
    "storage": storage_probe,
    "network": network_probe,
}

VALID_DEVICES = (
    "student_14_5",
    "handheld_hybrid",
    "ds_xl_coder",
    "wearables_arena_set",
)


def run_probes(
    device_id: str,
    *,
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    use_fixture = fixture_path is not None
    if fixture_path and fixture_path.exists():
        fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
        device_id = fixture_data.get("device_id", device_id)
        if "probes" in fixture_data:
            return fixture_data

    probes: dict[str, Any] = {}
    for name, mod in PROBE_MODULES.items():
        probes[name] = mod.probe(device_id, use_fixture=use_fixture)

    return {
        "device_id": device_id,
        "host_os": detect_host_os(),
        "host_environment": not use_fixture,
        "profile_source": "hardware_compat/device_profiles" if not use_fixture else "fixture",
        "fixture_path": str(fixture_path) if fixture_path else None,
        "probe_version": PROBE_VERSION,
        "claim_boundary": CLAIM,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "probes": probes,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="gunnchOS firmware host probe")
    ap.add_argument("--device", required=True, choices=VALID_DEVICES)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--fixture", type=Path, default=None, help="Explicit fixture JSON")
    args = ap.parse_args()

    result = run_probes(args.device, fixture_path=args.fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
