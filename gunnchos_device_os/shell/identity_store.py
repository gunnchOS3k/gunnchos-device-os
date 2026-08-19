"""Local-first identity persistence (Wave 002 / OS-PLATFORM-001)."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from gunnchos_device_os.identity import sha256_text
from gunnchos_device_os.unified_identity import (
    Account,
    AccountStatus,
    BindingState,
    DeviceBinding,
    DeviceRecord,
    Session,
    SessionState,
    UnifiedIdentityService,
)


class LocalIdentityStore:
    """Wraps UnifiedIdentityService with JSON file persistence."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "identity_store.json"
        self.service = UnifiedIdentityService()
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        svc = self.service
        for row in data.get("accounts", []):
            acct = Account(
                account_id=row["account_id"],
                display_name=row["display_name"],
                email_hash=row["email_hash"],
                roles=list(row.get("roles") or ["user"]),
                status=AccountStatus(row["status"]),
                created_at=row.get("created_at", ""),
            )
            svc.accounts[acct.account_id] = acct
        for row in data.get("devices", []):
            svc.devices[row["device_id"]] = DeviceRecord(
                device_id=row["device_id"],
                device_class=row["device_class"],
                label=row.get("label", ""),
                created_at=row.get("created_at", ""),
            )
        for row in data.get("bindings", []):
            svc.bindings[row["binding_id"]] = DeviceBinding(
                binding_id=row["binding_id"],
                account_id=row["account_id"],
                device_id=row["device_id"],
                state=BindingState(row["state"]),
                bound_at=row.get("bound_at", ""),
                trust_level=row.get("trust_level", "local"),
            )
        for row in data.get("sessions", []):
            svc.sessions[row["session_id"]] = Session(
                session_id=row["session_id"],
                account_id=row["account_id"],
                device_id=row["device_id"],
                binding_id=row["binding_id"],
                state=SessionState(row["state"]),
                issued_at_ms=int(row["issued_at_ms"]),
                expires_at_ms=int(row["expires_at_ms"]),
                token_hash=row["token_hash"],
                roles=list(row.get("roles") or []),
            )
        svc.audit = list(data.get("audit") or [])

    def save(self) -> None:
        svc = self.service
        payload = {
            "schema": "gunnchos.shell.identity_store.v1",
            "accounts": [a.to_dict() for a in svc.accounts.values()],
            "devices": [d.to_dict() for d in svc.devices.values()],
            "bindings": [b.to_dict() for b in svc.bindings.values()],
            "sessions": [s.to_dict() for s in svc.sessions.values()],
            "audit": list(svc.audit),
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def ensure_local_user(
        self,
        *,
        display_name: str = "Local User",
        email: str = "local@gunnchos.local",
        device_class: str = "handheld_hybrid",
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Bootstrap local-first user_id/profile_id/device_id/session material."""
        aid = f"acct-{sha256_text(email.lower().strip())[:12]}"
        acct = self.service.accounts.get(aid)
        if acct is None:
            acct = self.service.create_account(display_name, email, account_id=aid)
        user_id = f"user-{acct.account_id.split('-', 1)[-1]}"
        dev_id = f"dev-{device_class}"
        dev = self.service.devices.get(dev_id)
        if dev is None:
            dev = self.service.register_device(device_class, device_id=dev_id, label=display_name)
        binding = next(
            (
                b
                for b in self.service.bindings.values()
                if b.account_id == acct.account_id and b.device_id == dev.device_id and b.state.value == "bound"
            ),
            None,
        )
        if binding is None:
            binding = self.service.bind_device(acct.account_id, dev.device_id)
        active = next(
            (
                s
                for s in self.service.sessions.values()
                if s.account_id == acct.account_id and s.device_id == dev.device_id and s.state.value == "active"
            ),
            None,
        )
        if active is None:
            issued = self.service.issue_session(acct.account_id, dev.device_id)
            session_id = issued["session_id"]
        else:
            session_id = active.session_id
        self.save()
        return {
            "user_id": user_id,
            "profile_id": profile_id or f"profile-{acct.account_id}",
            "device_id": dev.device_id,
            "session_id": session_id,
            "account_id": acct.account_id,
            "binding_id": binding.binding_id,
            "authorized_devices": self.service.bindings_for_account(acct.account_id),
            "local_only": True,
            "storage_path": str(self.path),
        }

    def authorized_devices(self, account_id: str) -> list[dict[str, Any]]:
        return self.service.bindings_for_account(account_id)

    def revoke_device(self, binding_id: str) -> dict[str, Any]:
        result = self.service.unbind_device(binding_id)
        self.save()
        return result.to_dict()
