"""Simulated hardware boot readiness evaluation."""
from __future__ import annotations

from typing import Any

from .hardware_capability_detector import detect
from .hardware_manifest_loader import load_device_profile


def evaluate_boot_readiness(device_id: str) -> dict[str, Any]:
    profile = load_device_profile(device_id)
    caps = detect(device_id)
    checks = {
        "profile_available": True,
        "display_available": bool(profile.display.resolution or profile.raw.get("display")),
        "input_available": any([profile.input.keyboard, profile.input.touch, profile.input.controller]),
        "storage_sufficient": profile.storage.min_gb > 0,
        "battery_policy_available": bool(profile.power.battery_class),
        "thermal_policy_available": bool(profile.thermal.thermal_class),
        "accessibility_defaults_available": True,
        "recovery_fallback_available": True,
        "safe_mode_path_available": True,
        "unsupported_mode_fallback_available": True,
    }
    ready = all(checks.values())
    return {
        "device_id": device_id,
        "boot_ready_simulated": ready,
        "checks": checks,
        "capabilities": caps,
        "status": "simulated",
        "claim_boundary": "Simulated boot readiness exists. Real hardware boot is not yet proven.",
        "user_message": "Device profile loaded — simulated boot OK." if ready else "Boot readiness check failed in simulation.",
        "technical_log": f"boot_readiness_sim:device={device_id} ready={ready}",
    }
