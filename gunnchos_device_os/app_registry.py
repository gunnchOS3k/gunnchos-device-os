"""App registry — EVT-1 alpha with media metadata."""
from __future__ import annotations

from typing import Any

from .media_apps import MEDIA_APPS

APPS: dict[str, dict[str, Any]] = {
    "browser": {"category": "system", "name": "Browser", "launch_type": "browser_pwa"},
    "vscode": {"category": "developer", "name": "VS Code", "launch_type": "linux"},
    "terminal": {"category": "developer", "name": "Terminal", "launch_type": "linux"},
    "wsl_ubuntu": {"category": "developer", "name": "WSL Ubuntu", "launch_type": "linux"},
    "steam": {"category": "gaming", "name": "Steam", "launch_type": "linux"},
    "gunnchai3k": {"category": "education", "name": "gunnchAI3k", "launch_type": "native"},
    "waike_offline": {"category": "education", "name": "WAIKE Offline Lessons", "launch_type": "native"},
    "scaly_wings": {"category": "gaming", "name": "Scaly Wings", "launch_type": "native"},
    "scaly_wings_edu": {"category": "education", "name": "Scaly Wings Edu", "launch_type": "native"},
    "edgegesture": {"category": "gaming", "name": "EdgeGesture", "launch_type": "native"},
    "field_measurement": {"category": "research", "name": "Field Measurement", "launch_type": "native"},
    "edge_io": {"category": "research", "name": "Edge-IO Node", "launch_type": "native"},
}

# Merge structured media app metadata into registry.
for _media_id, _media_meta in MEDIA_APPS.items():
    APPS[_media_id] = {
        "category": "media",
        "name": _media_meta["name"],
        **_media_meta,
    }

CATEGORIES = ("education", "developer", "gaming", "media", "system", "research", "accessibility")


def list_apps(category: str | None = None) -> list[str]:
    if category is None:
        return sorted(APPS)
    return sorted(k for k, v in APPS.items() if v["category"] == category)


def get_app(app_id: str) -> dict[str, Any]:
    if app_id not in APPS:
        raise ValueError(f"Unknown app: {app_id}")
    return dict(APPS[app_id])
