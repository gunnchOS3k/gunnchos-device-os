"""Secure local Credential Wallet storage — canonical Wallet authority."""

from __future__ import annotations

import json
import os
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx3.contracts import validate_record
from gunnchos_device_os.cx3.issuer import verify_credential


class CredentialWallet:
    """File-backed wallet with restrictive perms; no private issuer keys stored."""

    def __init__(self, root: Path, *, owner_profile_id: str = "profile:lab-student"):
        self.root = Path(root)
        self.owner_profile_id = owner_profile_id
        self.creds_dir = self.root / "credentials"
        self.status_path = self.root / "status_index.json"
        self.meta_path = self.root / "wallet_meta.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.creds_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
            os.chmod(self.creds_dir, 0o700)
        except OSError:
            pass
        if not self.meta_path.is_file():
            self._write_json(
                self.meta_path,
                {
                    "schema": "gunnchos.cx3.wallet_meta.v1",
                    "owner_profile_id": owner_profile_id,
                    "created_at": _now(),
                    "certification_claimed": False,
                    "stores_issuer_private_keys": False,
                },
            )
        if not self.status_path.is_file():
            self._write_json(self.status_path, {"statuses": {}, "certification_claimed": False})

    @staticmethod
    def _write_json(path: Path, obj: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, indent=2) + "\n")
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def _read_json(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text())

    def put(self, credential: Dict[str, Any]) -> Dict[str, Any]:
        ok, errs = validate_record("CredentialRecord", credential)
        if not ok:
            raise ValueError(f"wallet_reject:{errs}")
        if credential.get("certification_claimed") is not False:
            raise ValueError("wallet_reject:certification_claimed")
        cid = credential["credential_id"]
        path = self.creds_dir / f"{_safe(cid)}.json"
        self._write_json(path, credential)
        statuses = self._read_json(self.status_path)
        statuses.setdefault("statuses", {})[cid] = {
            "credential_id": cid,
            "status": credential.get("status") or "active",
            "updated_at": _now(),
            "certification_claimed": False,
        }
        statuses["certification_claimed"] = False
        self._write_json(self.status_path, statuses)
        return {"ok": True, "credential_id": cid, "path": str(path)}

    def get(self, credential_id: str) -> Optional[Dict[str, Any]]:
        path = self.creds_dir / f"{_safe(credential_id)}.json"
        if not path.is_file():
            return None
        return self._read_json(path)

    def list(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for p in sorted(self.creds_dir.glob("*.json")):
            try:
                out.append(self._read_json(p))
            except Exception:
                continue
        return out

    def status_map(self) -> Dict[str, str]:
        data = self._read_json(self.status_path)
        return {k: v.get("status", "active") for k, v in (data.get("statuses") or {}).items()}

    def revoke(self, credential_id: str, *, reason: str = "lab_revoke") -> Dict[str, Any]:
        """Revoke via status index only — never mutate signed payload bytes."""
        cred = self.get(credential_id)
        if not cred:
            return {"ok": False, "blocker": "not_found"}
        statuses = self._read_json(self.status_path)
        statuses.setdefault("statuses", {})[credential_id] = {
            "credential_id": credential_id,
            "status": "revoked",
            "updated_at": _now(),
            "reason": reason,
            "certification_claimed": False,
        }
        statuses["certification_claimed"] = False
        self._write_json(self.status_path, statuses)
        return {"ok": True, "credential_id": credential_id, "status": "revoked"}

    def verify(self, credential_id: str, *, offline: bool = True) -> Dict[str, Any]:
        cred = self.get(credential_id)
        if not cred:
            return {"verified": False, "reasons": ["not_found"]}
        result = verify_credential(cred, status_lookup=self.status_map())
        result["offline"] = bool(offline)
        result["credential_id"] = credential_id
        return result

    def export_credentials(self, credential_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        all_creds = self.list()
        if credential_ids is not None:
            wanted = set(credential_ids)
            all_creds = [c for c in all_creds if c.get("credential_id") in wanted]
        # Strip nothing secret — wallet never holds issuer private keys
        export = {
            "export_id": f"cex:{uuid.uuid4().hex[:12]}",
            "format": "gunnchos.credential_export.v1",
            "credentials": all_creds,
            "exported_at": _now(),
            "certification_claimed": False,
            "include_private_keys": False,
            "owner_profile_id": self.owner_profile_id,
        }
        ok, errs = validate_record("CredentialExport", export)
        if not ok:
            raise ValueError(f"export_invalid:{errs}")
        return export

    def import_credentials(self, export_obj: Dict[str, Any]) -> Dict[str, Any]:
        if export_obj.get("certification_claimed") is not False:
            return {"ok": False, "blocker": "certification_claimed"}
        if export_obj.get("include_private_keys"):
            return {"ok": False, "blocker": "private_keys_forbidden"}
        ok, errs = validate_record("CredentialExport", export_obj)
        if not ok:
            return {"ok": False, "blocker": f"schema:{errs}"}
        imported = []
        rejected = []
        for cred in export_obj.get("credentials") or []:
            check = verify_credential(cred)
            if not check.get("verified") and cred.get("status") != "revoked":
                # Allow importing revoked if signature still validates against unsigned payload
                # but fail closed on tamper
                if check.get("tampered"):
                    rejected.append({"credential_id": cred.get("credential_id"), "reason": check.get("reasons")})
                    continue
            try:
                self.put(cred)
                imported.append(cred.get("credential_id"))
            except ValueError as exc:
                rejected.append({"credential_id": cred.get("credential_id"), "reason": str(exc)})
        return {
            "ok": len(rejected) == 0 and len(imported) > 0,
            "imported": imported,
            "rejected": rejected,
            "certification_claimed": False,
        }


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _safe(cid: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in cid)[:180]


def mint_wallet_token() -> str:
    return secrets.token_hex(16)
