"""Mock WSL dev tools checklist."""
from __future__ import annotations

RECOMMENDED_INSTALL = "wsl --install -d Ubuntu"
DEV_CHECKLIST = ["git", "python3", "node", "code", "docker (optional)"]


def detect_wsl() -> dict:
    # Mock detection — real impl would subprocess wsl -l -v
    return {"wsl_detected": False, "distros": [], "recommend": RECOMMENDED_INSTALL}


def checklist() -> list[str]:
    return list(DEV_CHECKLIST)
