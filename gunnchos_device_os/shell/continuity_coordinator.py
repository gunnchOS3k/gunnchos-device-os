"""Continuity coordinator + transparency disclosure (Wave 002 / OS-PLATFORM-007, OS-CONTINUITY-002–007)."""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.identity import sha256_bytes, sha256_json, utc_now_iso


CLAIM_BOUNDARY = (
    "Local-first session checkpoint store. Not cloud sync, not cross-vendor handoff, "
    "not physical device replacement."
)


@dataclass
class ContinuityDisclosure:
    """User-facing transparency for OS-CONTINUITY-002 through 007."""

    storage_root: Path

    def what_is_synchronized(self) -> dict[str, Any]:
        return {
            "synchronized": [
                "open_app_state",
                "input_remaps",
                "shell_form_factor",
                "lesson_progress_checkpoint",
            ],
            "not_synchronized": [
                "raw_biometrics",
                "cloud_llm_prompts",
                "vendor_hardware_serials",
            ],
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def where_stored(self) -> dict[str, Any]:
        return {
            "location": str(self.storage_root.resolve()),
            "medium": "local_json_files",
            "encrypted_at_rest": False,
            "cloud_replica": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def authorized_devices(self, bindings: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "authorized_devices": bindings,
            "policy": "explicit_device_binding_required",
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def what_remains_local(self) -> dict[str, Any]:
        return {
            "always_local": [
                "session_tokens",
                "checkpoint_payloads",
                "input_remap_tables",
                "audit_log",
            ],
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def how_to_revoke_device(self) -> dict[str, Any]:
        return {
            "steps": [
                "Open Settings → Devices → Authorized devices",
                "Select device → Revoke access",
                "Active sessions on revoked device are invalidated",
            ],
            "api": "ContinuityCoordinator.revoke_device(binding_id)",
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def how_to_export_or_delete(self) -> dict[str, Any]:
        return {
            "export": "ContinuityCoordinator.export_user_data(account_id) → JSON bundle",
            "delete": "ContinuityCoordinator.delete_user_data(account_id) removes checkpoints + identity store entries",
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def full_disclosure(self, bindings: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "OS-CONTINUITY-002": self.what_is_synchronized(),
            "OS-CONTINUITY-003": self.where_stored(),
            "OS-CONTINUITY-004": self.authorized_devices(bindings),
            "OS-CONTINUITY-005": self.what_remains_local(),
            "OS-CONTINUITY-006": self.how_to_revoke_device(),
            "OS-CONTINUITY-007": self.how_to_export_or_delete(),
        }


@dataclass
class ContinuityCoordinator:
    root: Path
    checkpoints: dict[str, dict[str, Any]] = field(default_factory=dict)
    conflicts: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "checkpoints.json"
        if self._index_path.exists():
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
            self.checkpoints = dict(data.get("checkpoints") or {})

    def _persist_index(self) -> None:
        self._index_path.write_text(
            json.dumps(
                {
                    "schema": "gunnchos.shell.continuity.v1",
                    "updated_at": utc_now_iso(),
                    "checkpoints": self.checkpoints,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def checkpoint(
        self,
        *,
        session_id: str,
        account_id: str,
        device_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        blob = json.dumps(payload, sort_keys=True).encode("utf-8")
        digest = sha256_bytes(blob)
        cp_id = f"cp-{digest[:16]}"
        path = self.root / f"{cp_id}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        meta = {
            "checkpoint_id": cp_id,
            "session_id": session_id,
            "account_id": account_id,
            "device_id": device_id,
            "content_sha256": digest,
            "created_at": utc_now_iso(),
            "path": str(path),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.checkpoints[cp_id] = meta
        self._persist_index()
        return meta

    def restore(self, checkpoint_id: str, *, expected_device_id: str | None = None) -> dict[str, Any]:
        meta = self.checkpoints.get(checkpoint_id)
        if meta is None:
            return {"ok": False, "error": "unknown_checkpoint"}
        if expected_device_id and meta["device_id"] != expected_device_id:
            return {"ok": False, "error": "device_mismatch", "expected": expected_device_id}
        path = Path(meta["path"])
        if not path.exists():
            return {"ok": False, "error": "payload_missing"}
        payload = json.loads(path.read_text(encoding="utf-8"))
        digest = sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
        if digest != meta["content_sha256"]:
            return {"ok": False, "error": "checksum_mismatch"}
        return {"ok": True, "checkpoint_id": checkpoint_id, "payload": payload, "meta": meta}

    def revoke_device(self, binding_id: str, identity_store: Any) -> dict[str, Any]:
        revoked = identity_store.revoke_device(binding_id)
        removed = [
            cp_id
            for cp_id, meta in list(self.checkpoints.items())
            if meta.get("device_id") == revoked.get("device_id")
        ]
        for cp_id in removed:
            path = Path(self.checkpoints[cp_id]["path"])
            if path.exists():
                path.unlink()
            del self.checkpoints[cp_id]
        self._persist_index()
        return {"revoked_binding": revoked, "checkpoints_removed": removed}

    def detect_conflict(self, local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
        local_hash = sha256_json(local)
        remote_hash = sha256_json(remote)
        if local_hash == remote_hash:
            return {"conflict": False}
        row = {
            "conflict": True,
            "local_sha256": local_hash,
            "remote_sha256": remote_hash,
            "detected_at": utc_now_iso(),
        }
        self.conflicts.append(row)
        return row

    def export_user_data(self, account_id: str) -> dict[str, Any]:
        rows = [m for m in self.checkpoints.values() if m.get("account_id") == account_id]
        bundle_dir = self.root / f"export-{account_id}-{int(time.time())}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        for meta in rows:
            src = Path(meta["path"])
            if src.exists():
                shutil.copy2(src, bundle_dir / src.name)
        manifest = {"account_id": account_id, "checkpoints": rows, "exported_at": utc_now_iso()}
        (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "bundle_dir": str(bundle_dir), "count": len(rows)}

    def delete_user_data(self, account_id: str) -> dict[str, Any]:
        removed = []
        for cp_id, meta in list(self.checkpoints.items()):
            if meta.get("account_id") != account_id:
                continue
            path = Path(meta["path"])
            if path.exists():
                path.unlink()
            del self.checkpoints[cp_id]
            removed.append(cp_id)
        self._persist_index()
        return {"ok": True, "removed_checkpoints": removed}

    def disclosure(self, bindings: list[dict[str, Any]]) -> dict[str, Any]:
        return ContinuityDisclosure(self.root).full_disclosure(bindings)
