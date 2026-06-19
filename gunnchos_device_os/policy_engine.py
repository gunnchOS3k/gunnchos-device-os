"""Policy engine — profile + mode decisions."""
from __future__ import annotations

from .mode_manager import get_mode_policy
from .profile_manager import get_profile


def evaluate(profile: str, mode: str, app: str) -> dict:
    prof = get_profile(profile)
    pol = get_mode_policy(mode)
    if mode not in prof["can_switch_to"] and profile != "admin":
        return {"allowed": False, "reason": "mode_not_permitted_for_profile"}
    allowed = app in pol["allowed_apps"]
    blocked = app in pol["blocked_apps"]
    if blocked:
        allowed = False
    needs_approval = profile in ("student", "guest") and mode == "Admin"
    return {
        "profile": profile,
        "mode": mode,
        "app": app,
        "allowed": allowed and not needs_approval,
        "telemetry": pol["telemetry"],
        "network": pol["network"],
        "content_restriction": pol["child_safety"],
        "admin_approval_required": needs_approval,
    }
