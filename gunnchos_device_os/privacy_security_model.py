"""Privacy and security model — consent, telemetry, and data minimization."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "privacy_defaults.yaml"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def get_profile_defaults(profile_type: str) -> dict[str, Any]:
    defaults = _load().get("defaults", {})
    key_map = {
        "child": "child_profile",
        "pre_k": "child_profile",
        "elementary": "child_profile",
        "school": "school_mode",
        "library": "library_mode",
        "research": "research_measurement",
        "research_operator": "research_measurement",
    }
    return defaults.get(key_map.get(profile_type, "adult_default"), defaults["adult_default"])


def get_telemetry_policy(profile_type: str, consent_state: str) -> dict[str, Any]:
    base = get_profile_defaults(profile_type)
    if consent_state == "denied":
        return {"category": "none", "enabled": False, "local_only": True}
    if profile_type in ("child", "pre_k", "elementary"):
        return {"category": "none", "enabled": False, "local_only": True}
    if base.get("requires_explicit_consent") and consent_state == "not_asked":
        return {"category": "none", "enabled": False, "consent_required": True}
    return {
        "category": base.get("telemetry_category", "local_diagnostics"),
        "enabled": consent_state.startswith("opt_in"),
        "local_only": base.get("local_only_mode", False),
    }


def request_export(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "status": "export_queued_placeholder",
        "path": "user_data_export_placeholder",
        "mock": True,
    }


def request_delete(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "status": "delete_queued_placeholder",
        "path": "user_data_delete_placeholder",
        "mock": True,
    }
