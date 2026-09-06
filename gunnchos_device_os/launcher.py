"""App launcher — policy gate plus first-party AppRuntime when cataloged.

Digital path only. Steam/browser/etc. remain policy-gated placeholders.
Not a shipping app store.

Learning OS (`waike_learning_os` / alias `waike_offline`) is handed off via
`learning_os_launcher` as a thin launcher/companion — seed HTML is not SoR.
"""
from __future__ import annotations

from typing import Any

from .app_registry import (
    APPS,
    LEARNING_OS_REGISTRY_ID,
    resolve_app_id,
)
from .app_runtime import RUNTIME_CATALOG, AppRuntime
from .diagnostics_log import log_event
from .permissions_manager import ROLE_ALLOWLIST
from .policy_engine import evaluate

# Registry ids → AppRuntime catalog ids (first-party digital apps only).
RUNTIME_ALIASES = {
    "waike_offline": "waike",
    LEARNING_OS_REGISTRY_ID: "waike",
}


def _runtime_id(app_id: str) -> str | None:
    mapped = RUNTIME_ALIASES.get(app_id, app_id)
    catalog = {app.id for app in RUNTIME_CATALOG}
    return mapped if mapped in catalog else None


def launch_app(profile: str, mode: str, app_id: str, *, thin_learning_os: bool = True) -> dict:
    if app_id not in APPS:
        result = {"launched": False, "reason": "unknown_app", "mock": False}
        log_event("app_launch_denied", {**result, "app": app_id, "mode": mode})
        return result

    # Canonical Learning OS path: thin launcher handoff (not seed-as-SoR).
    if thin_learning_os and resolve_app_id(app_id) == LEARNING_OS_REGISTRY_ID:
        from .learning_os_launcher import launch_learning_os

        return launch_learning_os(profile, mode, include_companion_seed=False)

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
        # Mark companion seed when this is the Learning OS runtime catalog entry.
        if runtime_id == "waike":
            result["relationship"] = "thin_launcher_companion"
            result["seed_is_system_of_record"] = False
            result["system_of_record"] = "platform_tauri_learning_os"
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
    """Single canonical implementation — includes alias→canonical mapping."""
    return [
        {
            "app": app_id,
            "allowed": evaluate(profile, mode, app_id)["allowed"],
            "runtime": _runtime_id(app_id) is not None,
            "canonical": resolve_app_id(app_id),
        }
        for app_id in sorted(APPS)
    ]
