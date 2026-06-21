"""User state store — in-memory profile persistence (prototype)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .user_profile_schema import UserProfile

_STORE: dict[str, UserProfile] = {}


def save_profile(profile: UserProfile, path: Path | None = None) -> None:
    _STORE[profile.user_id] = profile
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(profile.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_profile(user_id: str, path: Path | None = None) -> UserProfile | None:
    if user_id in _STORE:
        return _STORE[user_id]
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        profile = UserProfile.from_dict(data)
        _STORE[user_id] = profile
        return profile
    return None


def list_profiles() -> list[str]:
    return list(_STORE.keys())


def export_all(path: Path) -> dict[str, Any]:
    payload = {uid: p.to_dict() for uid, p in _STORE.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
