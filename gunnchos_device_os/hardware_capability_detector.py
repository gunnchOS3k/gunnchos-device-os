"""Simulated hardware capability detection — profile-based, not real probing."""
from __future__ import annotations

import argparse
from typing import Any

from .hardware_manifest_loader import load_device_profile, list_device_ids


def detect(device_id: str) -> dict[str, Any]:
    profile = load_device_profile(device_id)
    return {
        "device_id": device_id,
        "simulated": True,
        "detection_method": "profile_mirror",
        "capabilities": {
            "display": profile.raw.get("display", {}),
            "input": profile.raw.get("input", {}),
            "network": profile.raw.get("network", {}),
            "storage": profile.raw.get("storage", {}),
            "memory": profile.raw.get("memory", {}),
            "battery": profile.raw.get("battery", {}),
            "thermal": profile.raw.get("thermal", {}),
            "dock": profile.raw.get("dock", {}),
            "accessibility": profile.raw.get("accessibility", {}),
        },
        "supported_modes": profile.supported_modes,
        "claim_boundary": "Simulated detection from hardware_compat manifests — not real hardware probe",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulated hardware capability detector")
    parser.add_argument("--device", choices=list_device_ids(), required=True)
    args = parser.parse_args()
    import json
    print(json.dumps(detect(args.device), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
