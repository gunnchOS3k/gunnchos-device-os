"""WAIKE learning integration — EVT-1 alpha."""
from __future__ import annotations

OFFLINE_PACKS = [
    "waike_gary_upnow_intro",
    "wireless_basics_101",
    "python_starter_pack",
]


def list_offline_lessons() -> list[str]:
    return list(OFFLINE_PACKS)


def deploy_lesson(lesson_id: str, profile: str) -> dict:
    if lesson_id not in OFFLINE_PACKS:
        return {"deployed": False, "reason": "lesson_not_found"}
    return {
        "deployed": True,
        "lesson_id": lesson_id,
        "profile": profile,
        "offline_capable": True,
        "mock": True,
    }
