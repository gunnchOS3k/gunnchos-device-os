"""App registry — EVT-1 alpha with media metadata.

Learning OS is the canonical education app. `waike_offline` remains a
compatibility alias that resolves to `waike_learning_os`.
"""
from __future__ import annotations

from typing import Any

from .media_apps import MEDIA_APPS

# Compatibility aliases: legacy id → canonical registry id
COMPATIBILITY_ALIASES: dict[str, str] = {
    "waike_offline": "waike_learning_os",
}

# Platform Tauri bundle identity for the full native Learning OS LMS.
LEARNING_OS_BUNDLE_ID = "com.gunnchos.waike.learning"
LEARNING_OS_SDK_APP_ID = "gunnchos.waike_learning"
LEARNING_OS_RUNTIME_ID = "waike"
LEARNING_OS_REGISTRY_ID = "waike_learning_os"

APPS: dict[str, dict[str, Any]] = {
    "browser": {"category": "system", "name": "Browser", "launch_type": "browser_pwa"},
    "files": {
        "category": "system",
        "name": "Files",
        "launch_type": "native",
        "offline_supported": True,
        "workspace_backed": True,
        "claim_status": "browser_workspace_prototype",
    },
    "notes": {
        "category": "productivity",
        "name": "Notes",
        "launch_type": "native",
        "offline_supported": True,
        "workspace_backed": True,
        "claim_status": "browser_workspace_prototype",
    },
    "vscode": {"category": "developer", "name": "VS Code", "launch_type": "linux"},
    "terminal": {"category": "developer", "name": "Terminal", "launch_type": "linux"},
    "wsl_ubuntu": {"category": "developer", "name": "WSL Ubuntu", "launch_type": "linux"},
    "steam": {"category": "gaming", "name": "Steam", "launch_type": "linux"},
    "gunnchai3k": {"category": "education", "name": "gunnchAI3k", "launch_type": "native"},
    # Canonical Learning OS — Platform Tauri LMS is system of record.
    LEARNING_OS_REGISTRY_ID: {
        "category": "education",
        "name": "WAIKE Learning OS",
        "launch_type": "native",
        "bundle_id": LEARNING_OS_BUNDLE_ID,
        "sdk_app_id": LEARNING_OS_SDK_APP_ID,
        "runtime_id": LEARNING_OS_RUNTIME_ID,
        "role": "canonical_learning_os",
        "relationship": "thin_launcher_companion",
        "system_of_record": "platform_tauri_learning_os",
        "companion_seed_entry": "apps/waike_learning/index.html",
        "companion_role": "discovery_lab_seed_only",
        "claim_boundary": (
            "Device OS thin launcher/companion for Platform Learning OS. "
            "Seed HTML browser is discovery/lab only — not the LMS SoR."
        ),
    },
    # Compatibility alias — kept so School/Offline mode allowlists keep working.
    "waike_offline": {
        "category": "education",
        "name": "WAIKE Offline Lessons",
        "launch_type": "native",
        "alias_of": LEARNING_OS_REGISTRY_ID,
        "role": "compatibility_alias",
        "bundle_id": LEARNING_OS_BUNDLE_ID,
        "sdk_app_id": LEARNING_OS_SDK_APP_ID,
        "runtime_id": LEARNING_OS_RUNTIME_ID,
        "relationship": "thin_launcher_companion",
        "claim_boundary": (
            "Alias of waike_learning_os. Prefer the canonical id for new callers."
        ),
    },
    "scaly_wings": {"category": "gaming", "name": "Scaly Wings", "launch_type": "native"},
    "scaly_wings_edu": {"category": "education", "name": "Scaly Wings Edu", "launch_type": "native"},
    "edgegesture": {"category": "gaming", "name": "EdgeGesture", "launch_type": "native"},
    "field_measurement": {"category": "research", "name": "Field Measurement", "launch_type": "native"},
    "edge_io": {"category": "research", "name": "Edge-IO Node", "launch_type": "native"},
}

# Merge structured media app metadata into registry.
for _media_id, _media_meta in MEDIA_APPS.items():
    APPS[_media_id] = {
        "category": "media",
        "name": _media_meta["name"],
        **_media_meta,
    }

CATEGORIES = ("education", "developer", "gaming", "media", "system", "research", "accessibility")


def resolve_app_id(app_id: str) -> str:
    """Map compatibility aliases to the canonical registry id."""
    return COMPATIBILITY_ALIASES.get(app_id, app_id)


def app_id_equivalents(app_id: str) -> set[str]:
    """Return canonical id plus all aliases that resolve to it (incl. input)."""
    canonical = resolve_app_id(app_id)
    aliases = {k for k, v in COMPATIBILITY_ALIASES.items() if v == canonical}
    return {canonical, app_id} | aliases


def list_apps(category: str | None = None) -> list[str]:
    if category is None:
        return sorted(APPS)
    return sorted(k for k, v in APPS.items() if v["category"] == category)


def get_app(app_id: str, *, resolve_alias: bool = False) -> dict[str, Any]:
    if app_id not in APPS:
        raise ValueError(f"Unknown app: {app_id}")
    target_id = resolve_app_id(app_id) if resolve_alias else app_id
    if target_id not in APPS:
        raise ValueError(f"Unknown app: {target_id}")
    out = dict(APPS[target_id])
    out["app_id"] = target_id
    if app_id != target_id:
        out["requested_as"] = app_id
        out["resolved_from_alias"] = True
    return out
