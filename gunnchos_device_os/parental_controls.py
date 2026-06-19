"""Parental and school controls — EVT-1 alpha."""
from __future__ import annotations

from .mode_manager import get_mode_policy


def school_restrictions(mode: str) -> dict:
    pol = get_mode_policy(mode)
    return {
        "mode": mode,
        "child_safety": pol["child_safety"],
        "blocked_apps": pol["blocked_apps"],
        "network": pol["network"],
        "content_filter": pol["child_safety"] == "strict",
        "screen_time_limit_minutes": 120 if mode == "School" else None,
        "mock": True,
    }


def parental_override(parent_profile: str, action: str) -> dict:
    if parent_profile not in ("parent_guardian", "educator", "admin"):
        return {"approved": False, "reason": "insufficient_role"}
    return {"approved": True, "action": action, "audit_logged": True, "mock": True}


def content_report(reporter: str, category: str) -> dict:
    return {
        "received": True,
        "reporter_profile": reporter,
        "category": category,
        "escalation": "educator_review",
        "mock": True,
    }
