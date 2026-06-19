"""App registry — EVT-1 alpha."""
from __future__ import annotations

APPS: dict[str, dict] = {
    "browser": {"category": "system", "name": "Browser"},
    "vscode": {"category": "developer", "name": "VS Code"},
    "terminal": {"category": "developer", "name": "Terminal"},
    "wsl_ubuntu": {"category": "developer", "name": "WSL Ubuntu"},
    "steam": {"category": "gaming", "name": "Steam"},
    "youtube": {"category": "media", "name": "YouTube (browser)"},
    "netflix": {"category": "media", "name": "Netflix (browser)"},
    "hulu": {"category": "media", "name": "Hulu (browser)"},
    "gunnchai3k": {"category": "education", "name": "gunnchAI3k"},
    "waike_offline": {"category": "education", "name": "WAIKE Offline Lessons"},
    "scaly_wings": {"category": "gaming", "name": "Scaly Wings"},
    "scaly_wings_edu": {"category": "education", "name": "Scaly Wings Edu"},
    "edgegesture": {"category": "gaming", "name": "EdgeGesture"},
    "field_measurement": {"category": "research", "name": "Field Measurement"},
    "edge_io": {"category": "research", "name": "Edge-IO Node"},
}

CATEGORIES = ("education", "developer", "gaming", "media", "system", "research", "accessibility")


def list_apps(category: str | None = None) -> list[str]:
    if category is None:
        return sorted(APPS)
    return sorted(k for k, v in APPS.items() if v["category"] == category)
