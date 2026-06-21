#!/usr/bin/env python3
"""Simulate OS feature support on component stacks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACKS = ROOT / "configs" / "imported_component_stacks.yaml"
OUT = ROOT / "results" / "os_component_runtime_simulation.json"


def load_stacks() -> dict:
    text = STACKS.read_text()
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        return {}


def eval_device(device_id: str, spec: dict) -> dict:
    features = {}
    fallbacks = []
    ram = spec.get("ram_gb", 0)
    features["school_mode"] = ram >= 4
    features["developer_mode"] = ram >= 8 and not spec.get("developer_unrestricted") is False or device_id != "wearables_arena_set"
    if device_id == "wearables_arena_set":
        features["developer_mode"] = False
        fallbacks.append("marshal_controlled_play")
    features["wsl_path"] = bool(spec.get("wsl_capable")) and ram >= 16
    features["steam_path"] = bool(spec.get("steam_capable"))
    features["media_mode"] = True
    features["studio_mode"] = ram >= 8
    features["laboratory_mode"] = ram >= 8 and device_id != "wearables_arena_set"
    features["offline_mode"] = spec.get("storage_gb", 0) >= 64
    features["dock_external_display"] = spec.get("dock_dp_alt_mode") == "simulated" or spec.get("dock_dp_alt_mode") is True
    features["accessibility"] = True
    return {"device_id": device_id, "features": features, "fallbacks": fallbacks, "simulated": True}


def main() -> int:
    data = load_stacks()
    devices = data.get("devices") or data.get("stacks") or data
    results = [eval_device(d, s if isinstance(s, dict) else {}) for d, s in devices.items() if isinstance(s, dict)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"results": results, "simulated": True}, indent=2) + "\n")
    print(f"Wrote {OUT} ({len(results)} devices)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
