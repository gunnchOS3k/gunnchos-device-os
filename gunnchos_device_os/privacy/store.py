"""Local privacy data store — export, delete, retention, revocation.

Persists to a JSON file when a path is provided. Never writes raw secrets.
Not a production identity provider or cloud DSAR pipeline.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.privacy.policies import SURFACES


SCHEMA = "gunnchos.privacy.store.v1"


def _now_ms() -> int:
    return int(time.time() * 1000)


class PrivacyStore:
    """Per-user local records keyed by surface."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.users: dict[str, dict[str, Any]] = {}
        self.audit: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self._load()

    def _blank_user(self, user_id: str, profile_type: str) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "profile_type": profile_type,
            "created_at_ms": _now_ms(),
            "consent_state": "denied" if profile_type in ("child", "pre_k", "elementary") else "not_asked",
            "permissions": {},
            "guardian_grants": {},
            "surfaces": {s: [] for s in SURFACES},
            "revoked": False,
            "deleted": False,
        }

    def ensure_user(self, user_id: str, profile_type: str = "adult") -> dict[str, Any]:
        user = self.users.get(user_id)
        if user is None or user.get("deleted"):
            user = self._blank_user(user_id, profile_type)
            self.users[user_id] = user
            self._audit("ensure_user", {"user_id": user_id, "profile_type": profile_type})
            self.persist()
        return user

    def append(self, user_id: str, surface: str, record: dict[str, Any], *, profile_type: str = "adult") -> dict[str, Any]:
        if surface not in SURFACES:
            raise ValueError(f"unknown surface: {surface}")
        user = self.ensure_user(user_id, profile_type)
        if user.get("deleted") or user.get("revoked"):
            raise PermissionError("user_deleted_or_revoked")
        item = {"ts_ms": _now_ms(), **record}
        user["surfaces"][surface].append(item)
        self.persist()
        return item

    def set_permission(self, user_id: str, name: str, granted: bool, *, reason: str, guardian: bool = False) -> dict[str, Any]:
        user = self.ensure_user(user_id)
        grant = {
            "granted": granted,
            "reason": reason,
            "guardian": guardian,
            "at_ms": _now_ms(),
        }
        user["permissions"][name] = grant
        if guardian:
            user["guardian_grants"][name] = grant
        self._audit("set_permission", {"user_id": user_id, "name": name, **grant})
        self.persist()
        return grant

    def export_user(self, user_id: str) -> dict[str, Any]:
        user = self.users.get(user_id)
        if user is None:
            return {"user_id": user_id, "found": False, "surfaces": {}, "mock": False}
        payload = {
            "schema": SCHEMA,
            "user_id": user_id,
            "found": True,
            "profile_type": user.get("profile_type"),
            "consent_state": user.get("consent_state"),
            "permissions": dict(user.get("permissions") or {}),
            "surfaces": {k: list(v) for k, v in (user.get("surfaces") or {}).items()},
            "revoked": bool(user.get("revoked")),
            "deleted": bool(user.get("deleted")),
            "exported_at_ms": _now_ms(),
            "mock": False,
        }
        self._audit("export", {"user_id": user_id})
        return payload

    def delete_user(self, user_id: str) -> dict[str, Any]:
        user = self.ensure_user(user_id)
        wiped = {s: len(user["surfaces"].get(s) or []) for s in SURFACES}
        user["surfaces"] = {s: [] for s in SURFACES}
        user["permissions"] = {}
        user["guardian_grants"] = {}
        user["consent_state"] = "denied"
        user["revoked"] = True
        user["deleted"] = True
        user["deleted_at_ms"] = _now_ms()
        self._audit("delete", {"user_id": user_id, "wiped": wiped})
        self.persist()
        return {
            "user_id": user_id,
            "deleted": True,
            "revoked": True,
            "wiped": wiped,
            "mock": False,
        }

    def apply_retention(self, user_id: str, surface: str, max_age_ms: int, *, now_ms: int | None = None) -> int:
        user = self.users.get(user_id)
        if user is None:
            return 0
        now = now_ms if now_ms is not None else _now_ms()
        records = list(user["surfaces"].get(surface) or [])
        kept = [r for r in records if (now - int(r.get("ts_ms") or 0)) <= max_age_ms]
        dropped = len(records) - len(kept)
        user["surfaces"][surface] = kept
        if dropped:
            self.persist()
        return dropped

    def persist(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        blob = {"schema": SCHEMA, "users": self.users, "audit": self.audit[-200:]}
        self.path.write_text(json.dumps(blob, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _load(self) -> None:
        assert self.path is not None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.users = dict(data.get("users") or {})
        self.audit = list(data.get("audit") or [])

    def _audit(self, action: str, details: dict[str, Any]) -> None:
        self.audit.append({"action": action, "details": details, "ts_ms": _now_ms()})
