#!/usr/bin/env python3
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
HW_ROOT = ROOT.parent / "gunnchos-hardware-industrial-design"
DEVICES = ["student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set"]


def load_profile(device: str) -> dict:
    p = ROOT / "configs/devices" / f"{device}.yaml"
    if yaml and p.exists():
        return yaml.safe_load(p.read_text())
    return {"device_id": device}


def load_hw_contract(device: str) -> dict | None:
    c = HW_ROOT / "results/contracts" / f"{device}_hardware_profile.json"
    if c.exists():
        return json.loads(c.read_text())
    local = ROOT / "shared_contracts" / f"{device}_hardware_profile.json"
    return json.loads(local.read_text()) if local.exists() else None


def main() -> None:
    out = ROOT / "results/device_states"
    out.mkdir(parents=True, exist_ok=True)
    for d in DEVICES:
        state = {
            "device_id": d,
            "os_profile": load_profile(d),
            "hardware_profile": load_hw_contract(d),
            "optimized_mode": load_profile(d).get("default_mode", "school"),
            "readiness_level": "OS2",
            "evidence": "hardware_os_integration_stub",
        }
        (out / f"{d}_state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("Generated device states")


if __name__ == "__main__":
    main()
