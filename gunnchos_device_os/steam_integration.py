"""Mock Steam integration — licensing boundary documented."""
from __future__ import annotations

from pathlib import Path

STEAM_PATHS = [
    Path("C:/Program Files (x86)/Steam/steam.exe"),
    Path.home() / ".steam" / "steam" / "steam.sh",
]

PLACEHOLDER_GAMES = ["Scaly Wings (placeholder)", "EdgeGesture Demo (placeholder)"]


def detect_steam_installed() -> bool:
    return any(p.exists() for p in STEAM_PATHS)


def launch_uri(app_id: str = "0") -> str:
    return f"steam://run/{app_id}"


def list_placeholder_games() -> list[str]:
    return list(PLACEHOLDER_GAMES)
