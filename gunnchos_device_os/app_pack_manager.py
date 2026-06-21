"""App pack manager — curated app bundles by workflow."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_app_packs


def list_app_packs() -> list[str]:
    return list(load_app_packs().get("packs", {}).keys())


def get_app_pack(pack_id: str) -> dict[str, Any]:
    packs = load_app_packs().get("packs", {})
    if pack_id not in packs:
        raise ValueError(f"Unknown app pack: {pack_id}")
    return {"id": pack_id, **packs[pack_id]}


def get_packs_for_preset(preset_id: str) -> list[str]:
    packs = load_app_packs().get("packs", {})
    return [pid for pid, p in packs.items() if p.get("required_mode") == preset_id or preset_id in p.get("compatible_modes", [])]
