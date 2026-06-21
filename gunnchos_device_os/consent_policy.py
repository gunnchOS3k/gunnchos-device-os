"""Consent policy — explicit opt-in states."""
from __future__ import annotations

from typing import Any

from .privacy_security_model import get_telemetry_policy, _load


CONSENT_STATES = ("not_asked", "denied", "local_only", "opt_in_aggregate", "opt_in_research")


def set_consent(user_id: str, state: str, profile_type: str = "adult") -> dict[str, Any]:
    if state not in CONSENT_STATES:
        raise ValueError(f"Invalid consent state: {state}")
    telemetry = get_telemetry_policy(profile_type, state)
    return {
        "user_id": user_id,
        "consent_state": state,
        "telemetry": telemetry,
        "user_message": _consent_message(state),
        "technical_log": f"consent_set:user={user_id} state={state}",
        "mock": True,
    }


def _consent_message(state: str) -> str:
    messages = {
        "not_asked": "We have not asked for telemetry yet.",
        "denied": "Telemetry is off. Your data stays on this device.",
        "local_only": "Only local diagnostics are kept on this device.",
        "opt_in_aggregate": "You opted in to aggregated usage only.",
        "opt_in_research": "You opted in to research measurement metadata.",
    }
    return messages.get(state, "Consent updated.")


def research_requires_consent(profile_type: str, consent_state: str) -> bool:
    if profile_type in ("research", "research_operator"):
        return consent_state not in ("opt_in_research", "opt_in_aggregate")
    defaults = _load().get("defaults", {}).get("research_measurement", {})
    return defaults.get("requires_explicit_consent", True) and consent_state == "not_asked"
