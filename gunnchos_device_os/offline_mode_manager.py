"""Offline mode manager — low-bandwidth and disconnected workflows."""
from __future__ import annotations

from typing import Any

OFFLINE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "offline_lessons": {"apps": ["waike_offline", "gunnchai3k"], "sync": "when_online"},
    "offline_writing": {"apps": ["write_placeholder"], "sync": "when_online"},
    "offline_sketching": {"apps": ["sketch_placeholder"], "sync": "when_online"},
    "offline_coding": {"apps": ["vscode", "waike_offline"], "sync": "when_online"},
    "offline_music": {"apps": ["music_notes_placeholder"], "sync": "when_online"},
    "offline_games": {"apps": ["scaly_wings_edu"], "sync": "license_dependent"},
}


def get_offline_plan(profile_offline_first: bool = True) -> dict[str, Any]:
    return {
        "offline_first": profile_offline_first,
        "capabilities": OFFLINE_CAPABILITIES,
        "sync_when_online": True,
        "conflict_handling": "placeholder_last_write_wins",
        "mock": True,
    }


def enable_offline_mode(preset_id: str = "offline") -> dict[str, Any]:
    return {
        "preset": preset_id,
        "plan": get_offline_plan(True),
        "message": "Offline mode enabled — content syncs when connected",
    }
