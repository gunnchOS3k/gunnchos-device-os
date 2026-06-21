"""Mode policy engine — transitions, consent, and safety rules."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "modes.yaml"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def get_transition_rules() -> dict[str, Any]:
    return _load().get("transition_rules", {})


def can_transition(
    from_mode: str,
    to_mode: str,
    *,
    profile_type: str = "adult",
    guardian_approved: bool = False,
    consent_given: bool = False,
) -> dict[str, Any]:
    rules = get_transition_rules()
    child_rule = rules.get("child_to_unrestricted", {})
    if profile_type in ("child", "pre_k", "elementary", "middle_school"):
        blocked = child_rule.get("blocked_without_approval", [])
        if to_mode in blocked and not guardian_approved:
            return {
                "allowed": False,
                "reason": "guardian_approval_required",
                "user_message": "A guardian must approve switching to this mode.",
                "technical_log": f"mode_transition_blocked:from={from_mode} to={to_mode} profile={profile_type}",
            }

    school_rule = rules.get("school_library_silent_admin", {})
    if from_mode in ("School", "Library", "Guardian") and to_mode in school_rule.get("blocked_transitions", []):
        if not consent_given:
            return {
                "allowed": False,
                "reason": "explicit_consent_required",
                "user_message": "School and library devices need explicit approval for admin or developer modes.",
                "technical_log": f"mode_transition_blocked:school_library from={from_mode} to={to_mode}",
            }

    telemetry_rule = rules.get("telemetry_requires_consent", {})
    if to_mode in telemetry_rule.get("modes_requiring_consent", []) and not consent_given:
        return {
            "allowed": True,
            "telemetry_blocked_until_consent": True,
            "user_message": "This mode needs your consent before any telemetry starts.",
            "technical_log": f"mode_transition_consent_required:to={to_mode}",
        }

    return {
        "allowed": True,
        "user_message": f"Switched to {to_mode}.",
        "technical_log": f"mode_transition_ok:from={from_mode} to={to_mode}",
    }


def research_mode_policy() -> dict[str, Any]:
    rules = get_transition_rules()
    return {
        "no_private_payload": rules.get("research_no_private_payload", {}),
        "consent_required": True,
        "local_only_default": True,
    }
