"""IDENTITY — unified user/device/AI/MDM/Ring identity with login/lock/guest/roles/revoke.

Biometric hardware remains PHYSICAL_PENDING.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Unified software identity plane for user/device/AI/MDM/Ring. "
    "Biometric hardware PHYSICAL_PENDING. Not a production IdP."
)

ROLES = ("owner", "guardian", "student", "guest", "mdm_admin", "ai_agent", "ring")
IDENTITY_KINDS = ("user", "device", "ai", "mdm", "ring")


def _hash_secret(secret: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 50_000).hex()


@dataclass
class Principal:
    principal_id: str
    kind: str
    display_name: str
    roles: list[str] = field(default_factory=list)
    revoked: bool = False
    salt: str = ""
    secret_hash: str = ""


@dataclass
class Session:
    session_id: str
    principal_id: str
    state: str  # active | locked | guest | revoked
    roles: list[str]
    created_at: float
    locked_at: float | None = None


class UnifiedIdentityPlane:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.principals: dict[str, Principal] = {}
        self.sessions: dict[str, Session] = {}
        self.bindings: dict[str, list[str]] = {}  # principal -> device/ai/ring ids
        self.audit: list[dict[str, Any]] = []

    def _audit(self, op: str, **kwargs: Any) -> None:
        self.audit.append({"op": op, "at": time.time(), **kwargs})

    def register(
        self,
        principal_id: str,
        kind: str,
        display_name: str,
        roles: list[str],
        secret: str = "dev-secret",
    ) -> Principal:
        if kind not in IDENTITY_KINDS:
            raise ValueError(kind)
        for r in roles:
            if r not in ROLES:
                raise ValueError(r)
        salt = secrets.token_bytes(16)
        p = Principal(
            principal_id=principal_id,
            kind=kind,
            display_name=display_name,
            roles=list(roles),
            salt=salt.hex(),
            secret_hash=_hash_secret(secret, salt),
        )
        self.principals[principal_id] = p
        self.bindings.setdefault(principal_id, [])
        self._audit("register", principal_id=principal_id, kind=kind, roles=roles)
        return p

    def bind(self, principal_id: str, other_id: str) -> dict[str, Any]:
        if principal_id not in self.principals or other_id not in self.principals:
            raise KeyError("unknown_principal")
        self.bindings[principal_id].append(other_id)
        self._audit("bind", principal_id=principal_id, other_id=other_id)
        return {"ok": True, "principal_id": principal_id, "bound": other_id}

    def login(self, principal_id: str, secret: str) -> Session:
        p = self.principals[principal_id]
        if p.revoked:
            raise PermissionError("revoked")
        salt = bytes.fromhex(p.salt)
        if not hmac.compare_digest(_hash_secret(secret, salt), p.secret_hash):
            self._audit("login_fail", principal_id=principal_id)
            raise PermissionError("bad_secret")
        sid = secrets.token_hex(12)
        sess = Session(sid, principal_id, "active", list(p.roles), time.time())
        self.sessions[sid] = sess
        self._audit("login", principal_id=principal_id, session_id=sid)
        return sess

    def lock(self, session_id: str) -> Session:
        sess = self.sessions[session_id]
        sess.state = "locked"
        sess.locked_at = time.time()
        self._audit("lock", session_id=session_id)
        return sess

    def unlock(self, session_id: str, secret: str) -> Session:
        sess = self.sessions[session_id]
        p = self.principals[sess.principal_id]
        if p.revoked:
            raise PermissionError("revoked")
        salt = bytes.fromhex(p.salt)
        if not hmac.compare_digest(_hash_secret(secret, salt), p.secret_hash):
            raise PermissionError("bad_secret")
        sess.state = "active"
        sess.locked_at = None
        self._audit("unlock", session_id=session_id)
        return sess

    def guest_session(self) -> Session:
        gid = f"guest-{secrets.token_hex(4)}"
        self.register(gid, "user", "Guest", ["guest"], secret=secrets.token_hex(8))
        sid = secrets.token_hex(12)
        sess = Session(sid, gid, "guest", ["guest"], time.time())
        self.sessions[sid] = sess
        self._audit("guest", session_id=sid, principal_id=gid)
        return sess

    def revoke(self, principal_id: str) -> dict[str, Any]:
        p = self.principals[principal_id]
        p.revoked = True
        for sess in self.sessions.values():
            if sess.principal_id == principal_id:
                sess.state = "revoked"
        self._audit("revoke", principal_id=principal_id)
        return {"ok": True, "revoked": principal_id}

    def has_role(self, session_id: str, role: str) -> bool:
        sess = self.sessions[session_id]
        if sess.state in ("revoked", "locked"):
            return False
        return role in sess.roles

    def persist(self) -> Path:
        out = self.root / "IDENTITY_STATE.json"
        payload = {
            "principals": {k: asdict(v) for k, v in self.principals.items()},
            "sessions": {k: asdict(v) for k, v in self.sessions.items()},
            "bindings": self.bindings,
            "audit_tail": self.audit[-50:],
            "biometric_hw": "PHYSICAL_PENDING",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return out

    def e2e(self) -> dict[str, Any]:
        user = self.register("u-owner", "user", "Owner", ["owner", "student"], secret="s3cret")
        device = self.register("d-hh", "device", "Handheld", ["student"])
        ai = self.register("ai-local", "ai", "LocalAI", ["ai_agent"])
        mdm = self.register("mdm-1", "mdm", "SchoolMDM", ["mdm_admin"])
        ring = self.register("ring-1", "ring", "Ring", ["ring"])
        for other in (device.principal_id, ai.principal_id, mdm.principal_id, ring.principal_id):
            self.bind(user.principal_id, other)

        sess = self.login("u-owner", "s3cret")
        login_ok = sess.state == "active" and self.has_role(sess.session_id, "owner")

        locked = self.lock(sess.session_id)
        lock_ok = locked.state == "locked" and not self.has_role(sess.session_id, "owner")
        unlocked = self.unlock(sess.session_id, "s3cret")
        unlock_ok = unlocked.state == "active"

        guest = self.guest_session()
        guest_ok = guest.state == "guest" and self.has_role(guest.session_id, "guest")

        # Role denial
        role_denied = not self.has_role(guest.session_id, "mdm_admin")

        rev = self.revoke("u-owner")
        revoke_ok = rev["ok"] and self.sessions[sess.session_id].state == "revoked"
        login_blocked = False
        try:
            self.login("u-owner", "s3cret")
        except PermissionError:
            login_blocked = True

        path = self.persist()
        ok = all(
            [
                login_ok,
                lock_ok,
                unlock_ok,
                guest_ok,
                role_denied,
                revoke_ok,
                login_blocked,
                path.exists(),
                set(p.kind for p in self.principals.values()) >= set(IDENTITY_KINDS),
            ]
        )
        return {
            "schema": "gunnchos.phase_xv.identity.e2e.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "biometric_hw": "PHYSICAL_PENDING",
            "kinds": list(IDENTITY_KINDS),
            "roles": list(ROLES),
            "checks": {
                "login": login_ok,
                "lock": lock_ok,
                "unlock": unlock_ok,
                "guest": guest_ok,
                "role_denied": role_denied,
                "revoke": revoke_ok,
                "login_blocked": login_blocked,
            },
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
