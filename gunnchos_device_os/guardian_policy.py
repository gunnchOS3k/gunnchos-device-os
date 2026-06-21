"""Guardian policy — config-driven youth safety rules."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "guardian_defaults.yaml"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def get_age_band_policy(age_band: str) -> dict[str, Any]:
    bands = _load().get("age_bands", {})
    defaults = _load().get("defaults", {})
    band = bands.get(age_band, bands.get("elementary", {}))
    return {**defaults, "age_band": age_band, **band, "mock": True}


def approve_app(app_id: str, age_band: str, approved_list: list[str] | None = None) -> dict[str, Any]:
    policy = get_age_band_policy(age_band)
    if not policy.get("app_approval"):
        return {"approved": True, "app_id": app_id, "reason": "approval_not_required"}
    approved = approved_list or []
    allowed = app_id in approved
    return {
        "approved": allowed,
        "app_id": app_id,
        "user_message": "App approved." if allowed else "This app needs guardian approval first.",
        "technical_log": f"guardian_app_check:app={app_id} allowed={allowed}",
        "mock": True,
    }


def approve_mode(mode: str, age_band: str, guardian_approved: bool = False) -> dict[str, Any]:
    policy = get_age_band_policy(age_band)
    restricted = {"Developer", "Admin", "Workshop", "Laboratory"}
    if mode in restricted and policy.get("mode_approval") and not guardian_approved:
        return {
            "approved": False,
            "mode": mode,
            "user_message": "A guardian must approve this mode.",
            "technical_log": f"guardian_mode_blocked:mode={mode}",
            "mock": True,
        }
    return {"approved": True, "mode": mode, "mock": True}
