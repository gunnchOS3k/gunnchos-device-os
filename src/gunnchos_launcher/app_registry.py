"""App registry validation."""
from __future__ import annotations

APPS = [
    "WAIKE Classroom",
    "Ask gunnchAI3k",
    "Edge-IO Measurement",
    "7GC Digital Twin",
    "AI-RAN Lab",
    "Beam Selection Lab",
    "NTN Resilience Lab",
    "Code Dev Duck",
    "Arena Platform Fighter",
    "Deploy to Device",
    "Fleet Dashboard",
]


def validate_app(name: str) -> bool:
    return name in APPS


def list_apps() -> list[str]:
    return list(APPS)
