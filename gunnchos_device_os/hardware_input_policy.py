"""Hardware input policy."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ._hardware_policy_common import policy_result
from .hardware_manifest_loader import load_device_profile

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _matrix() -> dict:
    return yaml.safe_load((ROOT / "config/hardware_input_matrix.yaml").read_text())["requirements"]


def check_input(device_id: str, mode: str) -> dict:
    profile = load_device_profile(device_id)
    req = _matrix().get(mode, {})
    if not req:
        return policy_result("pass", "No special input requirement")
    if req.get("keyboard") and not profile.input.keyboard:
        if profile.raw.get("input", {}).get("keyboard") == "dock_optional":
            return policy_result("warn", "Keyboard via dock recommended", fallback="touch")
        return policy_result("fail", "Keyboard required but not primary input", fallback="School")
    if req.get("controller") and not profile.input.controller:
        return policy_result("warn", "Controller recommended for this mode")
    return policy_result("pass", "Input requirements met")
