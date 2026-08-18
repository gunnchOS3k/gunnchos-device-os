"""App launcher — policy gate plus first-party AppRuntime when cataloged.

Digital path only. Steam/browser/etc. remain policy-gated placeholders.
Not a shipping app store.
"""
from __future__ import annotations

from typing import Any

from .app_registry import APPS
from .app_runtime import RUNTIME_CATALOG, AppRuntime
from .diagnostics_log import log_event
from .permissions_manager import ROLE_ALLOWLIST
from .policy_engine import evaluate

# Registry ids → AppRuntime catalog ids (first-party digital apps only).
RUNTIME_ALIASES = {
    "waike_offline": "waike",
}


def _runtime_id(app_id: str) -> str | None:
    mapped = RUNTIME_ALIASES.get(app_id, app_id)
    catalog = {app.id for app in RUNTIME_CATALOG}
    return mapped if mapped in catalog else None


def launch_app(profile: str, mode: str, app_id: str) -> dict:
    if app_id not in APPS:
        result = {"launched": False, "reason": "unknown_app", "mock": False}
        log_event("app_launch_denied", {**result, "app": app_id, "mode": mode})
        return result
    decision = evaluate(profile, mode, app_id)
    if not decision["allowed"]:
        result = {
            "launched": False,
            "reason": "policy_denied",
            "decision": decision,
            "mock": False,
        }
        log_event("app_launch_denied", {"app": app_id, "mode": mode, "reason": "policy_denied"})
        return result

    runtime_id = _runtime_id(app_id)
    if runtime_id:
        runtime_role = profile if profile in ROLE_ALLOWLIST else "student"
        launched = AppRuntime(role=runtime_role).launch(runtime_id)
        result: dict[str, Any] = {
            "launched": bool(launched.get("ok")),
            "mock": False,
            "app": app_id,
            "runtime_id": runtime_id,
            "name": APPS[app_id]["name"],
            "category": APPS[app_id]["category"],
            "mode": mode,
            "profile": profile,
            "runtime": launched,
            "claim_boundary": (
                "Digital first-party AppRuntime via sandbox/permissions. "
                "Not a production app store."
            ),
        }
        if not result["launched"]:
            result["reason"] = launched.get("reason") or "runtime_launch_failed"
        log_event(
            "app_launch",
            {"app": app_id, "runtime_id": runtime_id, "ok": result["launched"], "mode": mode},
        )
        return result

    result = {
        "launched": True,
        "mock": True,
        "app": app_id,
        "name": APPS[app_id]["name"],
        "category": APPS[app_id]["category"],
        "mode": mode,
        "profile": profile,
        "claim_status": APPS[app_id].get("claim_status", "policy_gated_placeholder"),
    }
    log_event("app_launch_placeholder", {"app": app_id, "mode": mode})
    return result


def list_launchable(profile: str, mode: str) -> list[dict]:
    return [
        {
            "app": app_id,
            "allowed": evaluate(profile, mode, app_id)["allowed"],
            "runtime": _runtime_id(app_id) is not None,
        }
        for app_id in sorted(APPS)
    ]
