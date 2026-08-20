"""Parental, student, educator, and administrator profile policy orchestration."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.permissions_manager import Decision, Permission, PermissionGrant, PermissionsManager

PROFILE_TYPES = ("student", "educator", "guardian", "admin", "child", "minor", "guest")
SCHEMA_VERSION = 1
ADMIN_PROFILES = {"admin", "guardian"}


@dataclass
class RolePolicyService:
    """Maps OS-PLATFORM-023 profile roles to permission baselines with persistence."""

    storage_path: Path | None = None
    active_profiles: dict[str, str] = field(default_factory=dict)
    managers: dict[str, PermissionsManager] = field(default_factory=dict)
    pending_requests: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.storage_path is not None:
            self.storage_path = Path(self.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._load()

    def _state_file(self) -> Path:
        assert self.storage_path is not None
        return self.storage_path / "role_policy.json"

    def _load(self) -> None:
        path = self._state_file()
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.active_profiles = data.get("active_profiles", {})
        self.pending_requests = data.get("pending_requests", {})
        for user_id, profile in self.active_profiles.items():
            self.managers[user_id] = PermissionsManager(role=profile)

    def _persist(self) -> None:
        if self.storage_path is None:
            return
        payload = {
            "schema_version": SCHEMA_VERSION,
            "active_profiles": self.active_profiles,
            "pending_requests": self.pending_requests,
        }
        self._state_file().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def assign_profile(self, user_id: str, profile_type: str) -> dict[str, Any]:
        if profile_type not in PROFILE_TYPES:
            return {"ok": False, "error": "unknown_profile_type", "allowed": list(PROFILE_TYPES)}
        self.active_profiles[user_id] = profile_type
        self.managers[user_id] = PermissionsManager(role=profile_type)
        self._persist()
        return {"ok": True, "user_id": user_id, "profile_type": profile_type}

    def request_role_change(
        self,
        user_id: str,
        target_profile: str,
        *,
        requested_by: str,
    ) -> dict[str, Any]:
        if target_profile not in PROFILE_TYPES:
            return {"ok": False, "error": "unknown_profile_type"}
        current = self.active_profiles.get(user_id)
        if current is None:
            return {"ok": False, "error": "user_not_assigned"}
        if requested_by == user_id and target_profile in ADMIN_PROFILES:
            return {"ok": False, "error": "self_escalation_denied", "user_id": user_id}
        if requested_by == user_id and target_profile == "admin":
            return {"ok": False, "error": "self_escalation_denied", "user_id": user_id}
        request_id = uuid.uuid4().hex
        req = {
            "request_id": request_id,
            "user_id": user_id,
            "from_profile": current,
            "target_profile": target_profile,
            "requested_by": requested_by,
            "status": "pending",
            "requested_at_ms": int(time.time() * 1000),
        }
        self.pending_requests[request_id] = req
        self._persist()
        return {"ok": True, **req}

    def authorize_role_change(self, request_id: str, *, authorized_by: str) -> dict[str, Any]:
        req = self.pending_requests.get(request_id)
        if not req:
            return {"ok": False, "error": "request_not_found"}
        authorizer_profile = self.active_profiles.get(authorized_by)
        if authorizer_profile not in ADMIN_PROFILES:
            return {"ok": False, "error": "authorization_requires_admin_or_guardian"}
        if req["requested_by"] == req["user_id"] and req["target_profile"] in ADMIN_PROFILES:
            return {"ok": False, "error": "self_escalation_denied"}
        result = self.assign_profile(req["user_id"], req["target_profile"])
        req["status"] = "authorized"
        req["authorized_by"] = authorized_by
        req["authorized_at_ms"] = int(time.time() * 1000)
        self.pending_requests[request_id] = req
        self._persist()
        return {"ok": result.get("ok"), "request": req, "assignment": result}

    def deny_role_change(self, request_id: str, *, denied_by: str) -> dict[str, Any]:
        req = self.pending_requests.get(request_id)
        if not req:
            return {"ok": False, "error": "request_not_found"}
        authorizer_profile = self.active_profiles.get(denied_by)
        if authorizer_profile not in ADMIN_PROFILES:
            return {"ok": False, "error": "denial_requires_admin_or_guardian"}
        req["status"] = "denied"
        req["denied_by"] = denied_by
        self.pending_requests[request_id] = req
        self._persist()
        return {"ok": True, "request": req}

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
            "pending_requests": len(self.pending_requests),
        }

    @classmethod
    def from_storage(cls, storage_path: Path) -> "RolePolicyService":
        return cls(storage_path=storage_path)
