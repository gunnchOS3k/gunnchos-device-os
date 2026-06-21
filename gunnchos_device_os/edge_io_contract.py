"""Edge-IO measurement node integration contract."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "edge_io_contract.yaml"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def get_contract() -> dict[str, Any]:
    return _load()


def start_field_session(
    user_id: str,
    device_profile: str,
    *,
    consent: bool = False,
    research_operator: bool = False,
) -> dict[str, Any]:
    contract = _load()
    session = contract.get("session", {})
    if not consent:
        fm = contract.get("failure_modes", {}).get("consent_denied", {})
        return {
            "started": False,
            "user_message": fm.get("user_message", "Consent required."),
            "safe_fallback": fm.get("safe_fallback", "local_only"),
            "technical_log": "edge_io_session_blocked:no_consent",
            "next_action": fm.get("next_action", "return_to_launcher"),
        }
    if session.get("requires_research_operator") and not research_operator:
        return {
            "started": False,
            "user_message": "Research measurement needs a research operator profile.",
            "technical_log": "edge_io_session_blocked:not_research_operator",
            "next_action": "switch_profile",
        }
    return {
        "started": True,
        "user_id": user_id,
        "device_profile": device_profile,
        "metrics": contract.get("metrics", []),
        "local_only": session.get("local_only_default", True),
        "user_can_stop": session.get("user_can_stop", True),
        "technical_log": f"edge_io_session_start:user={user_id} device={device_profile}",
        "mock": True,
    }


def export_session(session_id: str, fmt: str = "json") -> dict[str, Any]:
    contract = _load()
    if fmt not in contract.get("session", {}).get("export_formats", []):
        fm = contract.get("failure_modes", {}).get("export_failed", {})
        return {
            "exported": False,
            "user_message": fm.get("user_message"),
            "technical_log": f"edge_io_export_failed:fmt={fmt}",
            "mock": True,
        }
    return {
        "exported": True,
        "session_id": session_id,
        "format": fmt,
        "path": f"edge_io_export_{session_id}.{fmt}",
        "no_private_payloads": True,
        "mock": True,
    }


def stop_session(session_id: str) -> dict[str, Any]:
    return {
        "stopped": True,
        "session_id": session_id,
        "user_message": "Measurement stopped.",
        "technical_log": f"edge_io_session_stop:{session_id}",
        "mock": True,
    }
