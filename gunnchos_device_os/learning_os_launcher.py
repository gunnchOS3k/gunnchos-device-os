"""Thin launcher / companion for the full native WAIKE Learning OS.

Device OS does not own the LMS. This module establishes the canonical
relationship: Device OS registers + policy-gates + deep-links + IPC-handshakes
into Platform's Tauri Learning OS (`com.gunnchos.waike.learning`).

The HTML seed at `apps/waike_learning/` is companion/discovery only — never
system of record.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from .app_registry import (
    LEARNING_OS_BUNDLE_ID,
    LEARNING_OS_REGISTRY_ID,
    LEARNING_OS_RUNTIME_ID,
    LEARNING_OS_SDK_APP_ID,
    get_app,
)
from .diagnostics_log import log_event
from .launcher import launch_app
from .permissions_manager import ROLE_ALLOWLIST, Permission, PermissionsManager
from .policy_engine import evaluate
from .rollback import rollback_to
from .shell.continuity_coordinator import ContinuityCoordinator
from .updater import check_for_update, check_learning_os_update

CLAIM_BOUNDARY = (
    "Device OS thin launcher/companion for Platform Learning OS. "
    "Seed HTML is discovery/lab only. Not a duplicate LMS."
)

DEEP_LINK_SCHEME = "waike"
ALLOWED_DEEP_LINK_KINDS = frozenset(
    {"learn", "section", "quiz", "assignment", "sync", "device"}
)
DEEP_LINK_PATTERN = re.compile(
    r"^waike://(learn|section|quiz|assignment|sync|device)(/[\w.\-/%]*)?$",
    re.IGNORECASE,
)

# Device OS role vocab ↔ Platform role vocab
PERMISSIONS_MAPPING: dict[str, dict[str, Any]] = {
    "student": {
        "platform_roles": ["learner", "grader"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["student"]),
    },
    "educator": {
        "platform_roles": ["instructor"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["educator"]),
    },
    "admin": {
        "platform_roles": ["site_admin"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["admin"]),
    },
    "guardian": {
        "platform_roles": ["guardian"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["guardian"]),
    },
    "guest": {
        "platform_roles": ["guest"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["guest"]),
    },
}

PLATFORM_TO_DEVICE_ROLE = {
    "learner": "student",
    "grader": "student",
    "instructor": "educator",
    "site_admin": "admin",
    "guardian": "guardian",
    "guest": "guest",
}

SECRET_KEYS = frozenset(
    {
        "password",
        "passwords",
        "private_key",
        "private_keys",
        "session_token",
        "session_tokens",
        "db_key",
        "db_keys",
        "lti_private_key",
        "lti_private_keys",
        "WAIKE_DEV_DB_KEY",
        "api_key",
        "secret",
    }
)


def resolve_learning_os_target(app_id: str | None = None) -> dict[str, Any]:
    """Resolve the canonical Learning OS launch target."""
    requested = app_id or LEARNING_OS_REGISTRY_ID
    known = {LEARNING_OS_REGISTRY_ID, "waike_offline", LEARNING_OS_RUNTIME_ID}
    lookup = requested if requested in (LEARNING_OS_REGISTRY_ID, "waike_offline") else LEARNING_OS_REGISTRY_ID
    if requested not in known and requested != LEARNING_OS_REGISTRY_ID:
        lookup = LEARNING_OS_REGISTRY_ID
    meta = get_app(lookup, resolve_alias=True)

    return {
        "registry_id": LEARNING_OS_REGISTRY_ID,
        "requested_id": requested,
        "resolved_id": LEARNING_OS_REGISTRY_ID,
        "runtime_id": LEARNING_OS_RUNTIME_ID,
        "sdk_app_id": LEARNING_OS_SDK_APP_ID,
        "bundle_id": LEARNING_OS_BUNDLE_ID,
        "deep_link_scheme": f"{DEEP_LINK_SCHEME}://",
        "relationship": "thin_launcher_companion",
        "system_of_record": "platform_tauri_learning_os",
        "companion_seed_entry": meta.get(
            "companion_seed_entry", "apps/waike_learning/index.html"
        ),
        "companion_role": "discovery_lab_seed_only",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def parse_deep_link(uri: str | None) -> dict[str, Any]:
    if not uri:
        return {"uri": None, "valid": True, "kind": None, "path": None}
    uri = uri.strip()
    if not DEEP_LINK_PATTERN.match(uri):
        return {"uri": uri, "valid": False, "reason": "scheme_or_kind_rejected"}
    if ".." in uri or "\\" in uri:
        return {"uri": uri, "valid": False, "reason": "path_traversal_rejected"}
    rest = uri[len("waike://") :]
    parts = rest.split("/", 1)
    kind = parts[0].lower()
    path = parts[1] if len(parts) > 1 else ""
    if kind not in ALLOWED_DEEP_LINK_KINDS:
        return {"uri": uri, "valid": False, "reason": "kind_rejected"}
    return {"uri": uri, "valid": True, "kind": kind, "path": path}


def ipc_handshake(
    *,
    profile: str,
    mode: str,
    deep_link: str | None = None,
    platform_role: str | None = None,
) -> dict[str, Any]:
    """Establish companion ↔ Learning OS IPC contract (digital)."""
    target = resolve_learning_os_target()
    link = parse_deep_link(deep_link)
    device_role = PLATFORM_TO_DEVICE_ROLE.get(platform_role or "", profile)
    if device_role not in ROLE_ALLOWLIST:
        device_role = profile if profile in ROLE_ALLOWLIST else "student"

    pm = PermissionsManager(role=device_role)
    grants = []
    for perm in (
        Permission.FILES_READ,
        Permission.NETWORK,
        Permission.IDENTITY_READ,
        Permission.NOTIFICATIONS,
    ):
        grants.append(
            pm.request(
                LEARNING_OS_SDK_APP_ID,
                perm,
                explicit_user_grant=perm in (
                    Permission.FILES_WRITE,
                    Permission.CAMERA,
                    Permission.MICROPHONE,
                ),
            )
        )

    return {
        "ok": link.get("valid", True),
        "protocol": "gunnchos.learning_os.ipc.v1",
        "allow_ipc": True,
        "launcher_role": "thin_launcher_companion",
        "learning_os_bundle_id": target["bundle_id"],
        "registry_id": target["registry_id"],
        "sdk_app_id": target["sdk_app_id"],
        "profile": profile,
        "device_role": device_role,
        "mode": mode,
        "deep_link": link,
        "permissions_grants": grants,
        "permissions_mapping": PERMISSIONS_MAPPING.get(device_role, PERMISSIONS_MAPPING["student"]),
        "seed_is_system_of_record": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def map_permissions_for_platform_role(platform_role: str) -> dict[str, Any]:
    device_role = PLATFORM_TO_DEVICE_ROLE.get(platform_role, "student")
    mapping = PERMISSIONS_MAPPING.get(device_role, PERMISSIONS_MAPPING["student"])
    pm = PermissionsManager(role=device_role)
    return {
        "platform_role": platform_role,
        "device_os_role": device_role,
        "allowlist": sorted(p.value for p in pm.allowlist()),
        "mapping": mapping,
        "authority": "device_os_permissions_manager",
    }


def _strip_secrets(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    removed: list[str] = []

    def _walk(obj: Any, path: str = "") -> Any:
        if isinstance(obj, dict):
            clean: dict[str, Any] = {}
            for k, v in obj.items():
                key_l = str(k).lower()
                if k in SECRET_KEYS or key_l in {s.lower() for s in SECRET_KEYS}:
                    removed.append(path + k)
                    continue
                if any(s.lower() in key_l for s in ("password", "private_key", "session_token", "secret", "api_key")):
                    removed.append(path + k)
                    continue
                clean[k] = _walk(v, path + k + ".")
            return clean
        if isinstance(obj, list):
            return [_walk(x, path) for x in obj]
        if isinstance(obj, str):
            upper = obj.upper()
            if "BEGIN PRIVATE" in upper or "WAIKE_DEV_DB_KEY" in upper:
                removed.append(path.rstrip(".") or "<string>")
                return "[REDACTED]"
        return obj

    return _walk(payload), removed


def continuity_handoff(
    *,
    from_profile: str,
    to_profile: str,
    account_id: str = "learning-os",
    session_id: str = "los-session",
    lesson_progress: dict[str, Any] | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """Checkpoint open app state via ContinuityCoordinator; secrets excluded."""
    raw_payload = {
        "open_app_state": {
            "app_id": LEARNING_OS_BUNDLE_ID,
            "registry_id": LEARNING_OS_REGISTRY_ID,
        },
        "lesson_progress_checkpoint": lesson_progress or {},
        "shell_form_factor": to_profile,
        "from_profile": from_profile,
    }
    clean, removed = _strip_secrets(raw_payload)
    # Reject if secrets were present in lesson_progress (fail closed for handoff)
    progress_blob = json.dumps(lesson_progress or {}).lower()
    for bad in ("password", "private_key", "session_token", "waike_dev_db_key", "begin private"):
        if bad in progress_blob:
            return {
                "ok": False,
                "contains_secrets": True,
                "reason": "CONTINUITY_SECRET_REJECTED",
                "claim_boundary": CLAIM_BOUNDARY,
            }

    root = storage_root or Path(tempfile.mkdtemp(prefix="waike-los-continuity-"))
    coord = ContinuityCoordinator(root=root)
    meta = coord.checkpoint(
        session_id=session_id,
        account_id=account_id,
        device_id=to_profile,
        payload=clean,
    )
    return {
        "ok": True,
        "contains_secrets": False,
        "secrets_stripped": removed,
        "checkpoint": meta,
        "payload": clean,
        "continuity_owner": "device_os_continuity_coordinator",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def invoke_updater_contract(current_version: str | None = None) -> dict[str, Any]:
    """Honest digital/mock updater check + rollback probe for Learning OS."""
    current = current_version or "0.0.9-evt0"
    device_update = check_for_update(current)
    los_update = check_learning_os_update(current_version or "0.1.0")
    rollback = rollback_to("0.0.9-evt0")
    return {
        "device_os_updater": device_update,
        "learning_os_updater": los_update,
        "rollback": rollback,
        "rollback_supported": bool(rollback.get("success")),
        "signing_truth": los_update.get("signing_truth", "UNSIGNED_DIGITAL_FIXTURE"),
        "update_owner": "platform_tauri_bundle",
        "claim_boundary": (
            "Digital/mock update contract only. Not production signed OTA."
        ),
    }


def launch_learning_os(
    profile: str,
    mode: str,
    deep_link: str | None = None,
    *,
    platform_role: str | None = None,
    include_companion_seed: bool = True,
) -> dict[str, Any]:
    """Thin-launcher handoff to Learning OS (canonical path).

    Returns a handoff descriptor — Learning OS Tauri app is system of record.
    Optionally surfaces the seed browser as companion/discovery only.
    """
    target = resolve_learning_os_target()
    link = parse_deep_link(deep_link)
    if deep_link and not link["valid"]:
        result = {
            "launched": False,
            "reason": "deep_link_rejected",
            "deep_link": link,
            "relationship": "thin_launcher_companion",
            "mock": False,
        }
        log_event("learning_os_launch_denied", result)
        return result

    decision = evaluate(profile, mode, LEARNING_OS_REGISTRY_ID)
    if not decision["allowed"]:
        # Fallback: legacy allowlist may only list waike_offline
        decision = evaluate(profile, mode, "waike_offline")
    if not decision["allowed"]:
        result = {
            "launched": False,
            "reason": "policy_denied",
            "decision": decision,
            "relationship": "thin_launcher_companion",
            "mock": False,
        }
        log_event("learning_os_launch_denied", result)
        return result

    handshake = ipc_handshake(
        profile=profile,
        mode=mode,
        deep_link=deep_link,
        platform_role=platform_role,
    )

    companion: dict[str, Any] | None = None
    if include_companion_seed:
        # Companion seed launch via existing AppRuntime path (discovery only).
        # Bypass thin-launcher recursion: seed path uses AppRuntime only.
        seed = launch_app(profile, mode, "waike_offline", thin_learning_os=False)
        companion = {
            "launched": seed.get("launched"),
            "entry": target["companion_seed_entry"],
            "role": "discovery_lab_seed_only",
            "is_system_of_record": False,
            "runtime": seed.get("runtime"),
            "runtime_id": seed.get("runtime_id"),
        }

    update = invoke_updater_contract()

    result = {
        "launched": True,
        "mock": False,
        "app": LEARNING_OS_REGISTRY_ID,
        "runtime_id": LEARNING_OS_RUNTIME_ID,
        "name": "WAIKE Learning OS",
        "category": "education",
        "relationship": "thin_launcher_companion",
        "launcher_wrapper_relationship": "thin_launcher_companion",
        "system_of_record": "platform_tauri_learning_os",
        "seed_is_system_of_record": False,
        "handoff": {
            "bundle_id": target["bundle_id"],
            "registry_id": target["registry_id"],
            "sdk_app_id": target["sdk_app_id"],
            "runtime_id": target["runtime_id"],
            "deep_link": link if deep_link else {"uri": "waike://learn/home", "kind": "learn", "path": "home", "valid": True},
            "ipc": handshake,
        },
        "target": target,
        "companion_seed": companion,
        "profile": profile,
        "mode": mode,
        "update_contract": {
            "invoked": True,
            "signing_truth": update["signing_truth"],
            "rollback_supported": update["rollback_supported"],
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }
    log_event(
        "learning_os_launch",
        {
            "ok": True,
            "bundle_id": target["bundle_id"],
            "mode": mode,
            "deep_link": deep_link,
        },
    )
    return result
