"""Device class model — hardware/software contract for gunnchOS devices."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "device_classes.yaml"

REQUIRED_FIELDS = (
    "device_id", "display_profile", "input_methods", "keyboard_support",
    "controller_support", "touch_support", "dock_support", "storage_class",
    "ram_target_gb", "performance_class", "battery_class", "thermal_class",
    "supported_journey_presets", "supported_modes", "supported_app_packs",
    "accessibility_defaults", "offline_capabilities", "deploy_role",
    "hardware_contract_assumptions",
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return data.get("device_classes", {})


def list_device_classes() -> list[str]:
    return list(_load().keys())


def get_device_class(class_id: str) -> dict[str, Any]:
    classes = _load()
    if class_id not in classes:
        raise ValueError(f"Unknown device class: {class_id}")
    return {"id": class_id, **classes[class_id]}


def validate_device_class(class_id: str) -> list[str]:
    dc = get_device_class(class_id)
    return [f for f in REQUIRED_FIELDS if f not in dc or dc[f] in (None, [], {})]
