"""Dock capability descriptors (no Pixel/USB-C DP Alt Mode assumptions)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CAPABILITIES: dict[str, Any] = {
    "descriptor_version": "1.0",
    "dock_classes": [
        {
            "id": "generic-usb-hub",
            "ports": ["usb-a", "usb-c"],
            "display": {"external_possible": True, "assumes_dp_alt_mode": False},
            "network": ["ethernet-optional"],
            "audio": ["headset-optional"],
            "power": {"passthrough_possible": True, "negotiated": False},
        },
        {
            "id": "generic-display-dock",
            "ports": ["usb-c", "hdmi-or-dp", "ethernet"],
            "display": {"external_possible": True, "assumes_dp_alt_mode": False},
            "network": ["ethernet"],
            "audio": ["hdmi-audio-optional", "3.5mm-optional"],
            "power": {"passthrough_possible": True, "negotiated": False},
        },
    ],
    "detection_policy": {
        "never_assume_vendor": True,
        "never_assume_pixel": True,
        "never_assume_usb_c_dp_alt_mode": True,
        "require_observed_capability": True,
    },
}


def load_capabilities(path: Path | str | None = None) -> dict[str, Any]:
    if path is None:
        candidate = Path("config/dock/capability_descriptors.json")
        if candidate.exists():
            path = candidate
        else:
            return dict(DEFAULT_CAPABILITIES)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("capability descriptors must be an object")
    return data


def describe_capability(caps: dict[str, Any], dock_class_id: str) -> dict[str, Any] | None:
    for item in caps.get("dock_classes", []):
        if item.get("id") == dock_class_id:
            return item
    return None
