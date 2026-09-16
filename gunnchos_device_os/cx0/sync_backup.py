"""SyncProvider + BackupProvider interfaces (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
import hashlib
import json
import time


@dataclass
class SyncProviderScaffold:
    provider_id: str = "gunnchos.cx0.sync_provider.v1"
    conflict_policy: str = "manual"
    scopes: List[str] = field(default_factory=lambda: ["user_files", "settings"])
    bandwidth_class: str = "offline_only"
    _queue: List[Dict] = field(default_factory=list)

    def enqueue(self, scope: str, payload: Dict) -> None:
        if scope not in self.scopes:
            raise ValueError(f"scope_not_allowed:{scope}")
        self._queue.append({"scope": scope, "payload": payload, "ts": time.time()})

    def pending_count(self) -> int:
        return len(self._queue)

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "conflict_policy": self.conflict_policy,
            "scopes": self.scopes,
            "bandwidth_class": self.bandwidth_class,
            "pending": self.pending_count(),
            "claim_boundary": "queue_scaffold_not_cloud_sync",
        }


@dataclass
class BackupProviderScaffold:
    provider_id: str = "gunnchos.cx0.backup_provider.v1"
    destinations: List[str] = field(default_factory=lambda: ["local"])
    encryption: str = "none"

    def backup_tree(self, source: Path, dest: Path) -> dict:
        dest.mkdir(parents=True, exist_ok=True)
        manifest = []
        for path in sorted(source.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(source))
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                data = path.read_bytes()
                target.write_bytes(data)
                manifest.append(
                    {"path": rel, "sha256": hashlib.sha256(data).hexdigest()}
                )
        meta = {
            "provider_id": self.provider_id,
            "encryption": self.encryption,
            "restore_verified": False,
            "files": manifest,
            "claim_boundary": "local_copy_scaffold_only",
        }
        (dest / "BACKUP_MANIFEST.json").write_text(json.dumps(meta, indent=2) + "\n")
        return meta

    def restore_tree(self, backup: Path, dest: Path) -> dict:
        manifest_path = backup / "BACKUP_MANIFEST.json"
        meta = json.loads(manifest_path.read_text())
        dest.mkdir(parents=True, exist_ok=True)
        for entry in meta["files"]:
            src = backup / entry["path"]
            out = dest / entry["path"]
            out.parent.mkdir(parents=True, exist_ok=True)
            data = src.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != entry["sha256"]:
                raise ValueError(f"checksum_mismatch:{entry['path']}")
            out.write_bytes(data)
        meta["restore_verified"] = True
        return meta
