"""Load hardware compatibility manifests from hardware_compat/device_profiles/."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .hardware_profile import (
    AccessibilityCapabilities,
    DeviceProfile,
    DisplayCapabilities,
    DockCapabilities,
    InputCapabilities,
    NetworkCapabilities,
    PowerCapabilities,
    StorageCapabilities,
    ThermalCapabilities,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "hardware_compat" / "device_profiles"

REQUIRED_TOP_LEVEL = (
    "device_id", "display", "input", "network", "storage", "memory",
    "battery", "thermal", "accessibility", "supported_modes",
    "supported_journey_presets", "supported_app_packs",
)


def list_device_ids() -> list[str]:
    return sorted(p.stem for p in PROFILE_DIR.glob("*.yaml"))


def _parse_profile(data: dict[str, Any]) -> DeviceProfile:
    display = data.get("display", {})
    inp = data.get("input", {})
    battery = data.get("battery", {})
    thermal = data.get("thermal", {})
    storage = data.get("storage", {})
    network = data.get("network", {})
    dock = data.get("dock", {})
    a11y = data.get("accessibility", {})
    return DeviceProfile(
        device_id=data["device_id"],
        display_name=data.get("display_name", data["device_id"]),
        display=DisplayCapabilities(
            size_inches=display.get("size_inches"),
            resolution=display.get("resolution", ""),
            external_display=display.get("external_display", False),
            touch=display.get("touch", False),
        ),
        input=InputCapabilities(
            keyboard=inp.get("keyboard", False),
            touch=inp.get("touch", False),
            controller=inp.get("controller", False),
            stylus=inp.get("stylus", False),
        ),
        power=PowerCapabilities(
            battery_class=battery.get("class", ""),
            school_day_target=battery.get("school_day_target", False),
        ),
        thermal=ThermalCapabilities(
            thermal_class=thermal.get("class", ""),
            throttle_policy=thermal.get("throttle_policy", ""),
        ),
        storage=StorageCapabilities(
            storage_class=storage.get("class", ""),
            min_gb=storage.get("min_gb", 0),
        ),
        memory_gb=data.get("memory", {}).get("ram_gb", 0),
        network=NetworkCapabilities(
            wifi=network.get("wifi", ""),
            offline_capable=network.get("offline_capable", True),
        ),
        dock=DockCapabilities(
            supported=dock.get("supported", False),
            usb_c_dp_alt_mode=dock.get("usb_c_dp_alt_mode", False),
        ),
        accessibility=AccessibilityCapabilities(
            screen_reader_labels=a11y.get("screen_reader_labels", True),
            controller_navigation=a11y.get("controller_navigation", False),
            high_contrast=a11y.get("high_contrast_default", False),
        ),
        supported_modes=data.get("supported_modes", []),
        supported_journey_presets=data.get("supported_journey_presets", []),
        supported_app_packs=data.get("supported_app_packs", []),
        known_gaps=data.get("known_gaps", []),
        hardware_repo_source_paths=data.get("hardware_repo_source_paths", []),
        claim_boundary=data.get("claim_boundary", ""),
        raw=data,
    )


def load_device_profile(device_id: str) -> DeviceProfile:
    path = PROFILE_DIR / f"{device_id}.yaml"
    if not path.exists():
        raise ValueError(f"Unknown hardware profile: {device_id}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in data]
    if missing:
        raise ValueError(f"Profile {device_id} missing fields: {missing}")
    return _parse_profile(data)


@lru_cache(maxsize=1)
def load_all_profiles() -> dict[str, DeviceProfile]:
    return {did: load_device_profile(did) for did in list_device_ids()}


def validate_profile(device_id: str) -> list[str]:
    errors: list[str] = []
    try:
        p = load_device_profile(device_id)
    except ValueError as e:
        return [str(e)]
    if not p.display.resolution and not p.raw.get("display"):
        errors.append("display missing")
    if not p.supported_modes:
        errors.append("supported_modes empty")
    return errors
