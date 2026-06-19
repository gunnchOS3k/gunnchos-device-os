"""App launcher — EVT-1 alpha."""
from __future__ import annotations

from .app_registry import APPS
from .policy_engine import evaluate


def launch_app(profile: str, mode: str, app_id: str) -> dict:
    if app_id not in APPS:
        return {"launched": False, "reason": "unknown_app"}
    decision = evaluate(profile, mode, app_id)
    if not decision["allowed"]:
        return {"launched": False, "reason": "policy_denied", "decision": decision}
    return {
        "launched": True,
        "mock": True,
        "app": app_id,
        "name": APPS[app_id]["name"],
        "category": APPS[app_id]["category"],
        "mode": mode,
        "profile": profile,
    }


def list_launchable(profile: str, mode: str) -> list[dict]:
    return [
        {"app": app_id, "allowed": evaluate(profile, mode, app_id)["allowed"]}
        for app_id in sorted(APPS)
    ]
