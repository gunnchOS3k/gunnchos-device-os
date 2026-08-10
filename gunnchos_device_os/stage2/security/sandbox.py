"""Sandbox profiles with bubblewrap when available, else file-backed simulation."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Permission(str, Enum):
    FS_HOME = "fs_home"
    FS_SYSTEM = "fs_system"
    NET = "net"
    DEVICE = "device"
    EXEC = "exec"


@dataclass
class SandboxProfile:
    app_id: str
    allow: set[Permission] = field(default_factory=set)
    deny: set[Permission] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "allow": sorted(p.value for p in self.allow),
            "deny": sorted(p.value for p in self.deny),
        }


class SandboxEnforcer:
    """Real bubblewrap when present; simulated file-backed denials in CI."""

    def __init__(self, state_dir: Path | str):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.denials_path = self.state_dir / "denials.jsonl"
        self.grants_path = self.state_dir / "grants.json"
        self.users_dir = self.state_dir / "users"
        self.users_dir.mkdir(exist_ok=True)
        self.audit_path = self.state_dir / "audit.log"
        self.secrets_dir = self.state_dir / "secrets"
        self.secrets_dir.mkdir(exist_ok=True)
        if not self.grants_path.exists():
            self.grants_path.write_text("{}\n")
        self.bwrap = shutil.which("bwrap")

    def bubblewrap_available(self) -> bool:
        return bool(self.bwrap)

    def _audit(self, event: str, detail: dict[str, Any]) -> None:
        line = json.dumps({"event": event, **detail})
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def set_profile(self, profile: SandboxProfile) -> None:
        grants = json.loads(self.grants_path.read_text() or "{}")
        grants[profile.app_id] = profile.to_dict()
        self.grants_path.write_text(json.dumps(grants, indent=2) + "\n")
        self._audit("profile_set", profile.to_dict())

    def revoke(self, app_id: str, perm: Permission) -> dict[str, Any]:
        grants = json.loads(self.grants_path.read_text() or "{}")
        entry = grants.get(app_id) or {"app_id": app_id, "allow": [], "deny": []}
        allow = set(entry.get("allow") or [])
        deny = set(entry.get("deny") or [])
        allow.discard(perm.value)
        deny.add(perm.value)
        entry["allow"] = sorted(allow)
        entry["deny"] = sorted(deny)
        grants[app_id] = entry
        self.grants_path.write_text(json.dumps(grants, indent=2) + "\n")
        self._audit("permission_revoked", {"app_id": app_id, "perm": perm.value})
        return entry

    def check(self, app_id: str, perm: Permission) -> dict[str, Any]:
        grants = json.loads(self.grants_path.read_text() or "{}")
        entry = grants.get(app_id)
        if not entry:
            decision = "deny"
            reason = "no_profile"
        elif perm.value in (entry.get("deny") or []):
            decision = "deny"
            reason = "explicit_deny"
        elif perm.value in (entry.get("allow") or []):
            decision = "allow"
            reason = "explicit_allow"
        else:
            decision = "deny"
            reason = "default_deny"
        rec = {
            "app_id": app_id,
            "perm": perm.value,
            "decision": decision,
            "reason": reason,
            "backend": "bwrap" if self.bwrap else "simulated",
        }
        if decision == "deny":
            with self.denials_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            self._audit("denial", rec)
        else:
            self._audit("allow", rec)
        return rec

    def isolate_user(self, user_id: str) -> Path:
        safe = self._safe_component(user_id)
        home = self.users_dir / safe
        home.mkdir(parents=True, exist_ok=True)
        (home / "PRIVATE").write_text(f"user={safe}\n")
        self._audit("user_isolated", {"user_id": safe, "home": safe})
        return home

    @staticmethod
    def _safe_component(value: str) -> str:
        if not value or value in {".", ".."} or "/" in value or "\\" in value or ".." in value:
            raise ValueError("unsafe_path_component")
        if value.startswith(".") or "\x00" in value:
            raise ValueError("unsafe_path_component")
        return value

    def secret_put(self, user_id: str, key: str, value: str, *, caller_id: str | None = None) -> None:
        safe_user = self._safe_component(user_id)
        safe_key = self._safe_component(key)
        caller = caller_id if caller_id is not None else safe_user
        if caller != safe_user:
            self._audit(
                "secret_put_denied",
                {"user_id": safe_user, "caller_id": caller, "reason": "cross_user"},
            )
            raise PermissionError("cross_user_secret_access")
        udir = self.secrets_dir / safe_user
        udir.mkdir(parents=True, exist_ok=True)
        (udir / f"{safe_key}.secret").write_text(value, encoding="utf-8")
        os.chmod(udir / f"{safe_key}.secret", 0o600)
        self._audit("secret_put", {"user_id": safe_user, "key": safe_key})

    def secret_get(self, user_id: str, key: str, *, caller_id: str | None = None) -> str | None:
        safe_user = self._safe_component(user_id)
        safe_key = self._safe_component(key)
        caller = caller_id if caller_id is not None else safe_user
        if caller != safe_user:
            self._audit(
                "secret_get_denied",
                {"user_id": safe_user, "caller_id": caller, "reason": "cross_user"},
            )
            raise PermissionError("cross_user_secret_access")
        path = self.secrets_dir / safe_user / f"{safe_key}.secret"
        # Defense in depth: resolved path must stay under secrets_dir.
        if not path.resolve().is_relative_to(self.secrets_dir.resolve()):
            raise PermissionError("path_escape")
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def try_bwrap_echo(self) -> dict[str, Any]:
        if not self.bwrap:
            return {"ok": False, "skipped": True, "reason": "bwrap_absent"}
        try:
            r = subprocess.run(
                [self.bwrap, "--ro-bind", "/", "/", "--dev", "/dev", "--", "echo", "ok"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "ok": r.returncode == 0 and "ok" in (r.stdout or ""),
                "exit_code": r.returncode,
                "backend": "bwrap",
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc), "backend": "bwrap"}
