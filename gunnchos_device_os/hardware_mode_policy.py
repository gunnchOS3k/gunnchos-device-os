"""Hardware mode policy."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ._hardware_policy_common import policy_result

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _matrix() -> dict:
    return yaml.safe_load((ROOT / "config/hardware_mode_matrix.yaml").read_text())["matrix"]


def check_mode(device_id: str, mode: str) -> dict:
    if not mode:
        return policy_result("pass", "No mode specified")
    allowed = _matrix().get(device_id, {}).get("allowed_modes", [])
    blocked = _matrix().get(device_id, {}).get("blocked_modes", [])
    if mode in blocked:
        fb = _matrix().get(device_id, {}).get("fallback_mode", "School")
        return policy_result(
            "fail",
            f"Mode {mode} is blocked on {device_id}",
            fallback=fb,
            evidence_required="hardware_mode_matrix_validation",
        )
    if allowed and mode not in allowed:
        return policy_result(
            "warn",
            f"Mode {mode} not in recommended list for {device_id}",
            fallback=allowed[0] if allowed else "Offline",
        )
    return policy_result("pass", f"Mode {mode} allowed on {device_id}")
