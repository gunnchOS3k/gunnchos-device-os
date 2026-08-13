"""Privacy and security model — consent, telemetry, and data minimization.

Export/delete are local DSAR operations via PrivacyController (not placeholders).
Not legal certification.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "privacy_defaults.yaml"
DEFAULT_STORE = ROOT / "results" / "privacy" / "store.json"


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


def _controller(persist: bool = True):
    from gunnchos_device_os.privacy.controller import PrivacyController

    path = DEFAULT_STORE if persist else None
    return PrivacyController(persist_path=path)


def request_export(user_id: str, dest: Path | None = None) -> dict[str, Any]:
    out = dest or (ROOT / "results" / "privacy" / f"{user_id}_export.json")
    return _controller().export(user_id, out)


def request_delete(user_id: str, dest: Path | None = None) -> dict[str, Any]:
    out = dest or (ROOT / "results" / "privacy" / f"{user_id}_delete.json")
    return _controller().delete(user_id, dest=out)
