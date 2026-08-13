"""Permissions manager — grant/deny API with least-privilege checks.

Software policy layer. Not a kernel sandbox or OS capability system.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
import time


class Permission(str, Enum):
    CAMERA = "camera"
    MICROPHONE = "microphone"
    LOCATION = "location"
    FILES_READ = "files_read"
    FILES_WRITE = "files_write"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    SENSORS = "sensors"
    NOTIFICATIONS = "notifications"
    AI_CLOUD_EXPORT = "ai_cloud_export"
    IDENTITY_READ = "identity_read"
    SCREEN_CAPTURE = "screen_capture"
    RING_INPUT = "ring_input"


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


# Role → maximum permissions (least privilege baselines)
ROLE_ALLOWLIST: dict[str, set[Permission]] = {
    "student": {
        Permission.FILES_READ,
        Permission.FILES_WRITE,
        Permission.NETWORK,
        Permission.NOTIFICATIONS,
        Permission.SENSORS,
        Permission.IDENTITY_READ,
    },
    "educator": {
        Permission.FILES_READ,
        Permission.FILES_WRITE,
        Permission.NETWORK,
        Permission.NOTIFICATIONS,
        Permission.CAMERA,
        Permission.MICROPHONE,
        Permission.SENSORS,
        Permission.IDENTITY_READ,
    },
    "guardian": {
        Permission.FILES_READ,
        Permission.NETWORK,
        Permission.NOTIFICATIONS,
        Permission.IDENTITY_READ,
    },
    "admin": set(Permission),
    "child": {
        Permission.FILES_READ,
        Permission.NOTIFICATIONS,
    },
    "minor": {
        Permission.FILES_READ,
        Permission.FILES_WRITE,
        Permission.NOTIFICATIONS,
        Permission.SENSORS,
        Permission.IDENTITY_READ,
    },
    "guest": {
        Permission.FILES_READ,
        Permission.NETWORK,
    },
    "ai_local": {
        Permission.FILES_READ,
        Permission.SENSORS,
        Permission.IDENTITY_READ,
    },
    "ai_cloud": {
        Permission.FILES_READ,
        Permission.NETWORK,
        Permission.AI_CLOUD_EXPORT,
        Permission.IDENTITY_READ,
    },
}

SENSITIVE = {
    Permission.CAMERA,
    Permission.MICROPHONE,
    Permission.LOCATION,
    Permission.AI_CLOUD_EXPORT,
    Permission.FILES_WRITE,
    Permission.SCREEN_CAPTURE,
    Permission.RING_INPUT,
}


@dataclass
class PermissionGrant:
    app_id: str
    permission: Permission
    decision: Decision
    role: str
    reason: str
    granted_at_ms: int
    expires_at_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["permission"] = self.permission.value
        d["decision"] = self.decision.value
        return d


@dataclass
class PermissionsManager:
    role: str = "student"
    grants: dict[tuple[str, str], PermissionGrant] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)
    deny_by_default: bool = True

    def set_role(self, role: str) -> None:
        if role not in ROLE_ALLOWLIST:
            raise ValueError(f"unknown role: {role}")
        self.role = role
        self._audit("set_role", {"role": role})

    def allowlist(self, role: str | None = None) -> set[Permission]:
        return set(ROLE_ALLOWLIST[role or self.role])

    def _audit(self, action: str, details: dict[str, Any]) -> None:
        self.audit.append(
            {
                "action": action,
                "details": details,
                "ts_ms": int(time.time() * 1000),
            }
        )

    def request(
        self,
        app_id: str,
        permission: Permission | str,
        *,
        role: str | None = None,
        explicit_user_grant: bool = False,
        ttl_ms: int | None = None,
    ) -> dict[str, Any]:
        perm = permission if isinstance(permission, Permission) else Permission(permission)
        effective_role = role or self.role
        allowlist = self.allowlist(effective_role)
        now = int(time.time() * 1000)

        if perm not in allowlist:
            grant = PermissionGrant(
                app_id=app_id,
                permission=perm,
                decision=Decision.DENY,
                role=effective_role,
                reason="outside_role_allowlist",
                granted_at_ms=now,
            )
            self.grants[(app_id, perm.value)] = grant
            self._audit("request_denied", grant.to_dict())
            return {**grant.to_dict(), "mock": False}

        if perm in SENSITIVE and not explicit_user_grant and effective_role not in ("admin", "educator"):
            grant = PermissionGrant(
                app_id=app_id,
                permission=perm,
                decision=Decision.DENY,
                role=effective_role,
                reason="sensitive_requires_explicit_grant",
                granted_at_ms=now,
            )
            self.grants[(app_id, perm.value)] = grant
            self._audit("request_denied", grant.to_dict())
            return {**grant.to_dict(), "mock": False}

        grant = PermissionGrant(
            app_id=app_id,
            permission=perm,
            decision=Decision.ALLOW,
            role=effective_role,
            reason="least_privilege_allow",
            granted_at_ms=now,
            expires_at_ms=(now + ttl_ms) if ttl_ms else None,
        )
        self.grants[(app_id, perm.value)] = grant
        self._audit("request_allowed", grant.to_dict())
        return {**grant.to_dict(), "mock": False}

    def revoke(self, app_id: str, permission: Permission | str) -> dict[str, Any]:
        perm = permission if isinstance(permission, Permission) else Permission(permission)
        key = (app_id, perm.value)
        existing = self.grants.pop(key, None)
        now = int(time.time() * 1000)
        grant = PermissionGrant(
            app_id=app_id,
            permission=perm,
            decision=Decision.DENY,
            role=self.role,
            reason="revoked",
            granted_at_ms=now,
        )
        self.grants[key] = grant
        self._audit("revoke", {"previous": existing.to_dict() if existing else None, **grant.to_dict()})
        return {**grant.to_dict(), "mock": False}

    def check(self, app_id: str, permission: Permission | str) -> dict[str, Any]:
        perm = permission if isinstance(permission, Permission) else Permission(permission)
        key = (app_id, perm.value)
        grant = self.grants.get(key)
        now = int(time.time() * 1000)
        if grant is None:
            decision = Decision.DENY if self.deny_by_default else Decision.ALLOW
            return {
                "app_id": app_id,
                "permission": perm.value,
                "decision": decision.value,
                "reason": "no_grant_deny_by_default" if self.deny_by_default else "no_grant_allow",
                "mock": False,
            }
        if grant.expires_at_ms is not None and now > grant.expires_at_ms:
            return {
                "app_id": app_id,
                "permission": perm.value,
                "decision": Decision.DENY.value,
                "reason": "grant_expired",
                "mock": False,
            }
        return {
            "app_id": app_id,
            "permission": perm.value,
            "decision": grant.decision.value,
            "reason": grant.reason,
            "mock": False,
        }

    def assert_allowed(self, app_id: str, permission: Permission | str) -> None:
        result = self.check(app_id, permission)
        if result["decision"] != Decision.ALLOW.value:
            raise PermissionError(
                f"{app_id} denied {permission}: {result['reason']}"
            )

    def least_privilege_report(self, app_id: str) -> dict[str, Any]:
        held = [
            g.to_dict()
            for (aid, _), g in self.grants.items()
            if aid == app_id and g.decision == Decision.ALLOW
        ]
        over_privileged = [
            g for g in held if Permission(g["permission"]) in SENSITIVE and g["role"] == "guest"
        ]
        return {
            "app_id": app_id,
            "role": self.role,
            "allowlist": sorted(p.value for p in self.allowlist()),
            "held": held,
            "over_privileged": over_privileged,
            "mock": False,
        }
