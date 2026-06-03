#!/usr/bin/env python3
"""Ensure shared contract schemas exist."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = [
    "hardware_os_device_profile.schema.json",
    "telemetry_contract.schema.json",
    "factory_test_contract.schema.json",
    "update_contract.schema.json",
    "fleet_policy_contract.schema.json",
]


def main() -> None:
    d = ROOT / "shared_contracts"
    d.mkdir(parents=True, exist_ok=True)
    for name in SCHEMAS:
        p = d / name
        if not p.exists():
            p.write_text(json.dumps({"type": "object", "title": name}, indent=2) + "\n", encoding="utf-8")
    print("Generated OS contracts")


if __name__ == "__main__":
    main()
