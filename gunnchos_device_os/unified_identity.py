"""Unified identity — account / session / device binding model.

Extends local device ID helpers with account-linked sessions and device
bindings. Software identity model only; not an IdP, SSO provider, or
hardware-backed credential store.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from gunnchos_device_os.identity import new_device_id, new_session_id, sha256_text, utc_now_iso


CLAIM_BOUNDARY = (
    "Software account/session/device binding model only. Not an identity "
    "provider, not SSO, not hardware-backed credentials."
)


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SessionState(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class BindingState(str, Enum):
    BOUND = "bound"
    UNBOUND = "unbound"
    REVOKED = "revoked"


@dataclass
class Account:
    account_id: str
    display_name: str
    email_hash: str  # never store raw email in this model
    roles: list[str] = field(default_factory=lambda: ["user"])
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class DeviceRecord:
    device_id: str
    device_class: str
    label: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceBinding:
    binding_id: str
    account_id: str
    device_id: str
    state: BindingState = BindingState.BOUND
    bound_at: str = field(default_factory=utc_now_iso)
    trust_level: str = "local"  # local | school | guardian_approved

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d


@dataclass
class Session:
    session_id: str
    account_id: str
    device_id: str
    binding_id: str
    state: SessionState = SessionState.ACTIVE
    issued_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    expires_at_ms: int = 0
    token_hash: str = ""
    roles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        # never expose raw token — only hash
        return d


@dataclass
class UnifiedIdentityService:
    """Account + device binding + session issuance/validation."""

    accounts: dict[str, Account] = field(default_factory=dict)
    devices: dict[str, DeviceRecord] = field(default_factory=dict)
    bindings: dict[str, DeviceBinding] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)
    default_session_ttl_ms: int = 3_600_000

    def _audit(self, action: str, details: dict[str, Any]) -> None:
        self.audit.append({"action": action, "details": details, "ts": utc_now_iso()})

    def create_account(
        self,
        display_name: str,
        email: str,
        *,
        roles: list[str] | None = None,
        account_id: str | None = None,
    ) -> Account:
        aid = account_id or f"acct-{sha256_text(email.lower())[:12]}"
        if aid in self.accounts:
            raise ValueError(f"account exists: {aid}")
        account = Account(
            account_id=aid,
            display_name=display_name,
            email_hash=sha256_text(email.lower().strip()),
            roles=list(roles or ["user"]),
        )
        self.accounts[aid] = account
        self._audit("create_account", {"account_id": aid, "roles": account.roles})
        return account

    def register_device(
        self,
        device_class: str,
        *,
        device_id: str | None = None,
        label: str = "",
    ) -> DeviceRecord:
        did = device_id or new_device_id(prefix=device_class[:6] or "dev")
        if did in self.devices:
            raise ValueError(f"device exists: {did}")
        rec = DeviceRecord(device_id=did, device_class=device_class, label=label)
        self.devices[did] = rec
        self._audit("register_device", rec.to_dict())
        return rec

    def bind_device(
        self,
        account_id: str,
        device_id: str,
        *,
        trust_level: str = "local",
    ) -> DeviceBinding:
        account = self.accounts.get(account_id)
        device = self.devices.get(device_id)
        if account is None:
            raise KeyError(f"unknown account: {account_id}")
        if device is None:
            raise KeyError(f"unknown device: {device_id}")
        if account.status != AccountStatus.ACTIVE:
            raise PermissionError("account_not_active")
        # One active binding per account+device
        for b in self.bindings.values():
            if (
                b.account_id == account_id
                and b.device_id == device_id
                and b.state == BindingState.BOUND
            ):
                return b
        binding_id = f"bind-{sha256_text(f'{account_id}:{device_id}:{secrets.token_hex(4)}')[:16]}"
        binding = DeviceBinding(
            binding_id=binding_id,
            account_id=account_id,
            device_id=device_id,
            trust_level=trust_level,
        )
        self.bindings[binding_id] = binding
        self._audit("bind_device", binding.to_dict())
        return binding

    def unbind_device(self, binding_id: str) -> DeviceBinding:
        binding = self.bindings.get(binding_id)
        if binding is None:
            raise KeyError(f"unknown binding: {binding_id}")
        binding.state = BindingState.REVOKED
        # Revoke sessions on this binding
        for sess in self.sessions.values():
            if sess.binding_id == binding_id and sess.state == SessionState.ACTIVE:
                sess.state = SessionState.REVOKED
        self._audit("unbind_device", binding.to_dict())
        return binding

    def issue_session(
        self,
        account_id: str,
        device_id: str,
        *,
        ttl_ms: int | None = None,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        account = self.accounts.get(account_id)
        if account is None or account.status != AccountStatus.ACTIVE:
            raise PermissionError("account_not_active")
        binding = next(
            (
                b
                for b in self.bindings.values()
                if b.account_id == account_id
                and b.device_id == device_id
                and b.state == BindingState.BOUND
            ),
            None,
        )
        if binding is None:
            raise PermissionError("device_not_bound_to_account")
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        ttl = ttl_ms if ttl_ms is not None else self.default_session_ttl_ms
        raw_token = secrets.token_urlsafe(24)
        session = Session(
            session_id=new_session_id(),
            account_id=account_id,
            device_id=device_id,
            binding_id=binding.binding_id,
            issued_at_ms=now,
            expires_at_ms=now + ttl,
            token_hash=sha256_text(raw_token),
            roles=list(account.roles),
        )
        self.sessions[session.session_id] = session
        self._audit(
            "issue_session",
            {"session_id": session.session_id, "account_id": account_id, "device_id": device_id},
        )
        # Return raw token once; stored form is hash only
        return {
            **session.to_dict(),
            "token": raw_token,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def validate_session(
        self,
        session_id: str,
        token: str,
        *,
        device_id: str | None = None,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        if session is None:
            return {
                "valid": False,
                "reason": "unknown_session",
                "mock": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        if session.state == SessionState.REVOKED:
            return {"valid": False, "reason": "revoked", "mock": False, "claim_boundary": CLAIM_BOUNDARY}
        if now > session.expires_at_ms:
            session.state = SessionState.EXPIRED
            return {"valid": False, "reason": "expired", "mock": False, "claim_boundary": CLAIM_BOUNDARY}
        if sha256_text(token) != session.token_hash:
            return {"valid": False, "reason": "bad_token", "mock": False, "claim_boundary": CLAIM_BOUNDARY}
        if device_id is not None and device_id != session.device_id:
            return {
                "valid": False,
                "reason": "device_mismatch",
                "mock": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        binding = self.bindings.get(session.binding_id)
        if binding is None or binding.state != BindingState.BOUND:
            return {
                "valid": False,
                "reason": "binding_revoked",
                "mock": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        return {
            "valid": True,
            "session_id": session.session_id,
            "account_id": session.account_id,
            "device_id": session.device_id,
            "roles": list(session.roles),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def revoke_session(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown session: {session_id}")
        session.state = SessionState.REVOKED
        self._audit("revoke_session", {"session_id": session_id})
        return {**session.to_dict(), "mock": False}

    def bindings_for_account(self, account_id: str) -> list[dict[str, Any]]:
        return [
            b.to_dict()
            for b in self.bindings.values()
            if b.account_id == account_id and b.state == BindingState.BOUND
        ]

    def status(self) -> dict[str, Any]:
        return {
            "accounts": len(self.accounts),
            "devices": len(self.devices),
            "bindings": len([b for b in self.bindings.values() if b.state == BindingState.BOUND]),
            "active_sessions": len(
                [s for s in self.sessions.values() if s.state == SessionState.ACTIVE]
            ),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
