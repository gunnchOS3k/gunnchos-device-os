"""Thin launcher / companion for the full native WAIKE Learning OS.

Device OS does not own the LMS. This module establishes the canonical
relationship: Device OS registers + policy-gates + deep-links + IPC-handshakes
into Platform's Tauri Learning OS (`com.gunnchos.waike.learning`).

The HTML seed at `apps/waike_learning/` is companion/discovery only — never
system of record.

`launched=True` is earned only after NativeLaunchAdapter succeeds (process +
IPC ack). Policy/dict metadata alone never claims launch.
"""
from __future__ import annotations

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
from .learning_os.continuity_policy import continuity_handoff_payload
from .learning_os.deep_link import (
    ALLOWED_DEEP_LINK_KINDS,
    DEEP_LINK_SCHEME,
    parse_deep_link,
)
from .learning_os.ipc_protocol import PROTOCOL_ID, build_launch_request
from .learning_os.ipc_transport import (
    DeterministicTestTransport,
    FileIpcTransport,
    IpcTransport,
)
from .learning_os.native_launch import NativeLaunchAdapter
from .learning_os.package_lifecycle import CLAIM_BOUNDARY as PACKAGE_CLAIM
from .learning_os.package_lifecycle import LearningOsPackageLifecycle
from .learning_os.provenance import build_provenance
from .learning_os.roles import (
    PERMISSIONS_MAPPING,
    PLATFORM_TO_DEVICE_ROLE,
    ROLE_MAPPING_DOC,
    map_permissions_for_platform_role,
)
from .permissions_manager import ROLE_ALLOWLIST, Permission, PermissionsManager
from .policy_engine import evaluate
from .shell.continuity_coordinator import ContinuityCoordinator
from .updater import check_for_update, check_learning_os_update

CLAIM_BOUNDARY = (
    "Device OS thin launcher/companion for Platform Learning OS. "
    "Seed HTML is discovery/lab only. Not a duplicate LMS. "
    "launched=True requires native launch adapter success."
)

# Re-exports for bridge/tests
__all__ = [
    "ALLOWED_DEEP_LINK_KINDS",
    "CLAIM_BOUNDARY",
    "DEEP_LINK_SCHEME",
    "PERMISSIONS_MAPPING",
    "PLATFORM_TO_DEVICE_ROLE",
    "ROLE_MAPPING_DOC",
    "continuity_handoff",
    "invoke_updater_contract",
    "ipc_handshake",
    "launch_learning_os",
    "map_permissions_for_platform_role",
    "parse_deep_link",
    "resolve_learning_os_target",
]


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


def ipc_handshake(
    *,
    profile: str,
    mode: str,
    deep_link: str | None = None,
    platform_role: str | None = None,
    transport: IpcTransport | None = None,
    timeout_s: float = 5.0,
    deliver: bool = True,
) -> dict[str, Any]:
    """Protocol schema + transport round-trip (not dict-only metadata).

    When deliver=False, returns schema/permission metadata without transport I/O
    (used for policy preflight). Production launch always delivers.
    """
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
                explicit_user_grant=False,
            )
        )

    context = {
        "profile": profile,
        "mode": mode,
        "device_role": device_role,
        "platform_role": platform_role,
        "registry_id": target["registry_id"],
        "bundle_id": target["bundle_id"],
        "sdk_app_id": target["sdk_app_id"],
        "runtime_id": target["runtime_id"],
    }
    request = build_launch_request(
        request_id="preflight",
        deep_link=link if deep_link else None,
        context={k: v for k, v in context.items() if v is not None},
        bundle_id=target["bundle_id"],
    )

    transport_result: dict[str, Any] | None = None
    if deliver:
        tx = transport or DeterministicTestTransport(auto_ack=True)
        # Unique request id for real delivery
        import uuid

        request = {**request, "request_id": str(uuid.uuid4())}
        if not link.get("valid", True):
            return {
                "ok": False,
                "protocol": PROTOCOL_ID,
                "allow_ipc": False,
                "reason": "deep_link_rejected",
                "deep_link": link,
                "transport": type(tx).__name__,
                "seed_is_system_of_record": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        transport_result = tx.send_and_await_ack(request, timeout_s=timeout_s)

    return {
        "ok": bool(transport_result.get("ok")) if transport_result else link.get("valid", True),
        "protocol": PROTOCOL_ID,
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
        "transport": type(transport).__name__ if transport else (
            type(DeterministicTestTransport).__name__ if deliver else None
        ),
        "transport_result": transport_result,
        "seed_is_system_of_record": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def continuity_handoff(
    *,
    from_profile: str,
    to_profile: str,
    account_id: str = "learning-os",
    session_id: str = "los-session",
    lesson_progress: dict[str, Any] | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    """Checkpoint open app state via ContinuityCoordinator; allowlist + no secrets."""
    filtered = continuity_handoff_payload(
        open_app_state={
            "app_id": LEARNING_OS_BUNDLE_ID,
            "registry_id": LEARNING_OS_REGISTRY_ID,
            "bundle_id": LEARNING_OS_BUNDLE_ID,
            "sdk_app_id": LEARNING_OS_SDK_APP_ID,
            "runtime_id": LEARNING_OS_RUNTIME_ID,
        },
        lesson_progress=lesson_progress,
        shell_form_factor=to_profile,
        from_profile=from_profile,
    )
    if not filtered["ok"]:
        return {
            "ok": False,
            "contains_secrets": True,
            "reason": filtered["reason"],
            "rejected_fields": filtered.get("rejected_fields", []),
            "dropped_fields": filtered.get("dropped_fields", []),
            "included_fields": [],
            "claim_boundary": CLAIM_BOUNDARY,
        }

    root = storage_root or Path(tempfile.mkdtemp(prefix="waike-los-continuity-"))
    coord = ContinuityCoordinator(root=root)
    meta = coord.checkpoint(
        session_id=session_id,
        account_id=account_id,
        device_id=to_profile,
        payload=filtered["payload"],
    )
    return {
        "ok": True,
        "contains_secrets": False,
        "secrets_stripped": filtered.get("dropped_fields", []),
        "included_fields": filtered.get("included_fields", []),
        "dropped_fields": filtered.get("dropped_fields", []),
        "checkpoint": meta,
        "payload": filtered["payload"],
        "continuity_owner": "device_os_continuity_coordinator",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def invoke_updater_contract(
    current_version: str | None = None,
    *,
    package_root: Path | None = None,
) -> dict[str, Any]:
    """Honest Learning OS package update/rollback probe.

    Uses PackageManager-backed LearningOsPackageLifecycle when package_root is
    provided or a default temp lifecycle exists. Never reports
    rollback_supported=True for mock rollback.py.
    """
    current = current_version or "0.0.9-evt0"
    device_update = check_for_update(current)
    los_update = check_learning_os_update(current_version or "0.1.0")

    lifecycle_status: dict[str, Any]
    if package_root is not None:
        life = LearningOsPackageLifecycle(package_root)
        lifecycle_status = life.status()
    else:
        lifecycle_status = {
            "installed": None,
            "executable": None,
            "rollback_supported": False,
            "claim_boundary": PACKAGE_CLAIM,
            "mock": False,
            "note": "no_package_root_configured",
        }

    return {
        "device_os_updater": device_update,
        "learning_os_updater": {
            **los_update,
            "rollback_supported": bool(lifecycle_status.get("rollback_supported")),
        },
        "package_lifecycle": lifecycle_status,
        "rollback": {
            "success": bool(lifecycle_status.get("rollback_supported")),
            "mock": False,
            "supported": bool(lifecycle_status.get("rollback_supported")),
            "claim_boundary": PACKAGE_CLAIM,
        },
        "rollback_supported": bool(lifecycle_status.get("rollback_supported")),
        "signing_truth": los_update.get("signing_truth", "UNSIGNED_DIGITAL_FIXTURE"),
        "update_owner": "platform_tauri_bundle_via_device_os_package_manager",
        "claim_boundary": PACKAGE_CLAIM,
    }


def launch_learning_os(
    profile: str,
    mode: str,
    deep_link: str | None = None,
    *,
    platform_role: str | None = None,
    include_companion_seed: bool = True,
    adapter: NativeLaunchAdapter | None = None,
    transport: IpcTransport | None = None,
    install_root: Path | None = None,
) -> dict[str, Any]:
    """Thin-launcher handoff to Learning OS (canonical path).

    launched=True only after native launch adapter succeeds.
    Seed companion is never treated as SoR and never flips launched.
    """
    target = resolve_learning_os_target()
    link = parse_deep_link(deep_link)
    stages = {
        "registered": True,
        "available": False,
        "handoff_created": False,
        "launch_attempted": False,
        "process_started": False,
        "deep_link_delivered": False,
        "acknowledged": False,
        "launched": False,
    }

    if deep_link and not link["valid"]:
        result = {
            **stages,
            "launched": False,
            "reason": "deep_link_rejected",
            "deep_link": link,
            "relationship": "thin_launcher_companion",
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        log_event("learning_os_launch_denied", result)
        return result

    decision = evaluate(profile, mode, LEARNING_OS_REGISTRY_ID)
    if not decision["allowed"]:
        decision = evaluate(profile, mode, "waike_offline")
    if not decision["allowed"]:
        result = {
            **stages,
            "launched": False,
            "reason": "policy_denied",
            "decision": decision,
            "relationship": "thin_launcher_companion",
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        log_event("learning_os_launch_denied", result)
        return result

    # Preflight permissions / role mapping (no claim of launch)
    handshake_meta = ipc_handshake(
        profile=profile,
        mode=mode,
        deep_link=deep_link,
        platform_role=platform_role,
        deliver=False,
    )

    companion: dict[str, Any] | None = None
    if include_companion_seed:
        seed = launch_app(profile, mode, "waike_offline", thin_learning_os=False)
        companion = {
            "launched": seed.get("launched"),
            "entry": target["companion_seed_entry"],
            "role": "discovery_lab_seed_only",
            "is_system_of_record": False,
            "runtime": seed.get("runtime"),
            "runtime_id": seed.get("runtime_id"),
        }

    native = adapter or NativeLaunchAdapter(
        install_root=install_root,
        transport=transport,
    )
    native_result = native.launch(
        deep_link=deep_link or "waike://learn/home",
        profile=profile,
        mode=mode,
        context={
            "device_role": handshake_meta.get("device_role"),
            "platform_role": platform_role,
        },
    )
    nd = native_result.to_dict()
    for key in stages:
        if key in nd:
            stages[key] = nd[key]

    update = invoke_updater_contract(package_root=install_root)

    result = {
        **stages,
        "mock": False,
        "app": LEARNING_OS_REGISTRY_ID,
        "runtime_id": LEARNING_OS_RUNTIME_ID,
        "name": "WAIKE Learning OS",
        "category": "education",
        "relationship": "thin_launcher_companion",
        "launcher_wrapper_relationship": "thin_launcher_companion",
        "system_of_record": "platform_tauri_learning_os",
        "seed_is_system_of_record": False,
        "reason": nd.get("reason"),
        "handoff": {
            "bundle_id": target["bundle_id"],
            "registry_id": target["registry_id"],
            "sdk_app_id": target["sdk_app_id"],
            "runtime_id": target["runtime_id"],
            "deep_link": link
            if deep_link
            else {
                "uri": "waike://learn/home",
                "canonical": "waike://learn/home",
                "kind": "learn",
                "path": "home",
                "valid": True,
            },
            "ipc": {
                **handshake_meta,
                "transport_result": nd.get("ipc"),
            },
            "native": {
                "pid": nd.get("pid"),
                "executable": nd.get("executable"),
                "version": nd.get("version"),
                "artifact_hash": nd.get("artifact_hash"),
            },
        },
        "target": target,
        "companion_seed": companion,
        "profile": profile,
        "mode": mode,
        "provenance": nd.get("provenance") or build_provenance(),
        "update_contract": {
            "invoked": True,
            "signing_truth": update["signing_truth"],
            "rollback_supported": update["rollback_supported"],
            "claim_boundary": update["claim_boundary"],
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }
    log_event(
        "learning_os_launch",
        {
            "ok": result["launched"],
            "bundle_id": target["bundle_id"],
            "mode": mode,
            "deep_link": deep_link,
            "reason": result.get("reason"),
        },
    )
    return result
