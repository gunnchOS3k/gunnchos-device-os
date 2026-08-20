"""Parental, student, educator, and administrator profile policy orchestration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import time

from gunnchos_device_os.permissions_manager import Decision, Permission, PermissionGrant, PermissionsManager

PROFILE_TYPES = ("student", "educator", "guardian", "admin", "child", "minor", "guest")


@dataclass
class RolePolicyService:
    """Maps OS-PLATFORM-023 profile roles to permission baselines."""

    active_profiles: dict[str, str] = field(default_factory=dict)
    managers: dict[str, PermissionsManager] = field(default_factory=dict)

    def assign_profile(self, user_id: str, profile_type: str) -> dict[str, Any]:
        if profile_type not in PROFILE_TYPES:
            return {"ok": False, "error": "unknown_profile_type", "allowed": list(PROFILE_TYPES)}
        self.active_profiles[user_id] = profile_type
        self.managers[user_id] = PermissionsManager(role=profile_type)
        return {"ok": True, "user_id": user_id, "profile_type": profile_type}

    def check_app_permission(self, user_id: str, app_id: str, permission: str) -> dict[str, Any]:
        profile = self.active_profiles.get(user_id)
        if not profile:
            return {"ok": False, "error": "user_not_assigned"}
        mgr = self.managers[user_id]
        try:
            perm = Permission(permission)
        except ValueError:
            return {"ok": False, "error": "unknown_permission"}
        result = mgr.request(app_id, perm)
        return {"ok": True, "profile_type": profile, **result}

    def guardian_override(self, user_id: str, app_id: str, permission: str, *, allow: bool) -> dict[str, Any]:
        profile = self.active_profiles.get(user_id)
        if profile not in ("child", "minor", "student"):
            return {"ok": False, "error": "guardian_override_requires_minor_profile"}
        mgr = self.managers[user_id]
        try:
            perm = Permission(permission)
        except ValueError:
            return {"ok": False, "error": "unknown_permission"}
        if allow:
            now = int(time.time() * 1000)
            grant = PermissionGrant(
                app_id=app_id,
                permission=perm,
                decision=Decision.ALLOW,
                role=profile,
                reason="guardian_override",
                granted_at_ms=now,
            )
            mgr.grants[(app_id, perm.value)] = grant
            result = grant.to_dict()
        else:
            result = mgr.revoke(app_id, perm)
            result["reason"] = "guardian_deny"
        return {"ok": True, "guardian_override": True, **result}

    def status(self) -> dict[str, Any]:
        return {
            "schema": "gunnchos.platform.role_policy.v1",
            "profile_types": list(PROFILE_TYPES),
            "assigned_users": len(self.active_profiles),
            "profiles": dict(self.active_profiles),
        }
