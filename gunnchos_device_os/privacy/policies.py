"""Enforceable privacy policies — surfaces, roles, retention, minimization.

Software policy only. Not legal certification, COPPA/FERPA/GDPR compliance,
or EXTERNAL counsel approval.
"""
from __future__ import annotations

from typing import Any


CLAIM_BOUNDARY = (
    "Digital privacy policy enforcement for gunnchOS device-os. "
    "Not legal certification. Legal approval remains HUMAN/EXTERNAL. "
    "Does not claim COPPA, FERPA, GDPR, or production privacy readiness."
)

SURFACES = (
    "accounts",
    "telemetry",
    "ai_context",
    "ai_memory",
    "voice",
    "vision",
    "screen",
    "ring",
    "waike",
    "games",
    "diagnostics",
)

CHILD_PROFILES = frozenset({"child", "pre_k", "elementary"})
MINOR_PROFILES = frozenset({"minor", "teen"})
GUARDIAN_REQUIRED_PROFILES = CHILD_PROFILES | MINOR_PROFILES

# Sensor / capture permissions that default-deny for youth.
SENSITIVE_SENSORS = frozenset({"voice", "vision", "screen", "ring"})

# Retention in days. 0 = session-only (wipe on export-complete / logout / delete).
RETENTION_DAYS: dict[str, dict[str, int]] = {
    "child": {
        "accounts": 0,
        "telemetry": 0,
        "ai_context": 0,
        "ai_memory": 0,
        "voice": 0,
        "vision": 0,
        "screen": 0,
        "ring": 0,
        "waike": 30,
        "games": 30,
        "diagnostics": 7,
    },
    "minor": {
        "accounts": 90,
        "telemetry": 7,
        "ai_context": 1,
        "ai_memory": 1,
        "voice": 0,
        "vision": 0,
        "screen": 0,
        "ring": 30,
        "waike": 90,
        "games": 90,
        "diagnostics": 14,
    },
    "adult": {
        "accounts": 365,
        "telemetry": 30,
        "ai_context": 30,
        "ai_memory": 30,
        "voice": 0,
        "vision": 0,
        "screen": 0,
        "ring": 180,
        "waike": 365,
        "games": 365,
        "diagnostics": 30,
    },
}

# Child/minor cannot enable these even with self-consent.
YOUTH_HARD_DENY = frozenset(
    {
        "telemetry_cloud",
        "ai_cloud_export",
        "voice_cloud",
        "vision_cloud",
        "screen_cloud",
        "game_social_public",
        "diagnostics_unredacted_export",
    }
)


def profile_family(profile_type: str) -> str:
    if profile_type in CHILD_PROFILES:
        return "child"
    if profile_type in MINOR_PROFILES:
        return "minor"
    if profile_type in ("school", "library"):
        return "minor" if profile_type == "school" else "child"
    return "adult"


def retention_days(profile_type: str, surface: str) -> int:
    family = profile_family(profile_type)
    table = RETENTION_DAYS.get(family, RETENTION_DAYS["adult"])
    return int(table.get(surface, 0))


def requires_guardian(profile_type: str, action: str) -> bool:
    family = profile_family(profile_type)
    if family == "child":
        return action in SENSITIVE_SENSORS or action in {
            "export",
            "ai_cloud_export",
            "telemetry_opt_in",
            "account_create_named",
        }
    if family == "minor":
        return action in SENSITIVE_SENSORS or action in {"ai_cloud_export", "telemetry_cloud"}
    return False


def minimization_rules() -> dict[str, Any]:
    return {
        "no_private_payload": True,
        "no_hidden_telemetry": True,
        "no_keystroke_logging": True,
        "no_message_content": True,
        "no_raw_email_in_logs": True,
        "no_student_name_in_diagnostics": True,
        "voice_default": "off",
        "vision_default": "off",
        "screen_capture_default": "deny",
        "ring_pair_default": "authenticated_only",
        "ai_cloud_default": "deny",
        "games_social_default": "local_only",
        "waike_pii_default": "local_progress_only",
    }
