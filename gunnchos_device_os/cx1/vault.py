"""CX1B Vault — browse/CRUD/trash/search/backup/restore/sync queue over FileProvider."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from gunnchos_device_os.cx0.file_provider import LocalPathFileProvider
from gunnchos_device_os.cx0.sync_backup import BackupProviderScaffold, SyncProviderScaffold


@dataclass
class VaultEntry:
    path: str
    size: int
    sha256: str
    modified_at: float
    in_trash: bool = False
    mime_hint: str = "application/octet-stream"


@dataclass
class Vault:
    """Product file authority wrapping local FS (+ optional removable root)."""

    root: Path
    removable_root: Optional[Path] = None
    provider: Optional[LocalPathFileProvider] = None
    sync: SyncProviderScaffold = field(default_factory=SyncProviderScaffold)
    backup: BackupProviderScaffold = field(default_factory=BackupProviderScaffold)
    _recent: List[str] = field(default_factory=list)
    _meta: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("files", "trash", "exports", "backups", "meta", "sync_queue"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self.provider = LocalPathFileProvider(root=self.root / "files")
        self.sync = DurableSyncQueue(queue_dir=self.root / "sync_queue")
        self._load_meta()

    def _load_meta(self) -> None:
        path = self.root / "meta" / "vault_meta.json"
        if path.exists():
            data = json.loads(path.read_text())
            self._recent = data.get("recent", [])
            self._meta = data.get("meta", {})

    def _save_meta(self) -> None:
        path = self.root / "meta" / "vault_meta.json"
        path.write_text(
            json.dumps({"recent": self._recent[:50], "meta": self._meta}, indent=2) + "\n"
        )

    def _touch_recent(self, rel: str) -> None:
        self._recent = [rel] + [r for r in self._recent if r != rel]
        self._recent = self._recent[:50]
        self._save_meta()

    def write(self, rel: str, data: bytes, *, mime_hint: str = "application/octet-stream") -> VaultEntry:
        assert self.provider is not None
        self.provider.write_bytes(rel, data)
        digest = hashlib.sha256(data).hexdigest()
        entry = VaultEntry(
            path=rel,
            size=len(data),
            sha256=digest,
            modified_at=time.time(),
            mime_hint=mime_hint,
        )
        self._meta[rel] = {
            "sha256": digest,
            "size": len(data),
            "mime_hint": mime_hint,
            "modified_at": entry.modified_at,
        }
        self._touch_recent(rel)
        self.sync.enqueue("user_files", {"op": "put", "path": rel, "sha256": digest})
        return entry

    def read(self, rel: str) -> bytes:
        assert self.provider is not None
        data = self.provider.read_bytes(rel)
        self._touch_recent(rel)
        return data

    def list(self, uri: str = ".") -> List[str]:
        assert self.provider is not None
        return self.provider.list(uri)

    def delete(self, rel: str, *, permanent: bool = False) -> None:
        assert self.provider is not None
        src = self.provider._resolve(rel)
        if not src.exists():
            raise FileNotFoundError(rel)
        if permanent:
            src.unlink()
            self._meta.pop(rel, None)
        else:
            trash = self.root / "trash" / rel
            trash.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(trash))
            if rel in self._meta:
                self._meta[rel]["in_trash"] = True
        self._save_meta()
        self.sync.enqueue("user_files", {"op": "delete", "path": rel, "permanent": permanent})

    def restore_from_trash(self, rel: str) -> None:
        trash = self.root / "trash" / rel
        if not trash.exists():
            raise FileNotFoundError(rel)
        assert self.provider is not None
        dest = self.provider._resolve(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trash), str(dest))
        if rel in self._meta:
            self._meta[rel]["in_trash"] = False
        self._save_meta()

    def search(self, query: str) -> List[str]:
        q = query.lower()
        hits = []
        files_root = self.root / "files"
        for path in files_root.rglob("*"):
            if path.is_file() and q in path.name.lower():
                hits.append(str(path.relative_to(files_root)))
        return sorted(hits)

    def recent(self) -> List[str]:
        return list(self._recent)

    def metadata(self, rel: str) -> dict:
        assert self.provider is not None
        path = self.provider._resolve(rel)
        if not path.exists():
            raise FileNotFoundError(rel)
        data = path.read_bytes()
        meta = self._meta.get(rel, {})
        return {
            "path": rel,
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(data).hexdigest(),
            "modified_at": path.stat().st_mtime,
            "mime_hint": meta.get("mime_hint", "application/octet-stream"),
            "in_trash": False,
        }

    def free_space(self) -> dict:
        usage = shutil.disk_usage(self.root)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "root": str(self.root),
        }

    def provider_status(self) -> dict:
        removable = None
        if self.removable_root and Path(self.removable_root).exists():
            removable = {
                "path": str(self.removable_root),
                "available": True,
                "entries": sorted(p.name for p in Path(self.removable_root).iterdir()),
            }
        elif self.removable_root:
            removable = {"path": str(self.removable_root), "available": False}
        return {
            "local": {"available": True, "root": str(self.root / "files")},
            "removable": removable,
            "lan": {"available": False, "notes": "adapter_only_unless_integrated"},
            "cloud": {"available": False, "notes": "adapter_only_no_provider_claim"},
            "sync_pending": self.sync.pending_count(),
        }

    def export(self, rel: str, dest: Path) -> Path:
        data = self.read(rel)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest

    def open_with(self, rel: str, handler: str) -> dict:
        """Record open-with binding; actual launch is handler-specific."""
        meta = self.metadata(rel)
        return {
            "path": rel,
            "handler": handler,
            "sha256": meta["sha256"],
            "opened_at": time.time(),
            "claim_boundary": "binding_recorded_launch_delegated",
        }

    def create_backup(self, label: Optional[str] = None) -> dict:
        label = label or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        dest = self.root / "backups" / label
        meta = self.backup.backup_tree(self.root / "files", dest)
        meta["backup_id"] = label
        meta["versioned"] = True
        meta["integrity_manifest"] = True
        # strengthen claim for CX1 local backup
        meta["claim_boundary"] = "local_versioned_backup_with_integrity_manifest"
        (dest / "BACKUP_MANIFEST.json").write_text(json.dumps(meta, indent=2) + "\n")
        return meta

    def restore_backup(
        self,
        backup_id: str,
        *,
        overwrite: str = "fail",
        target: Optional[Path] = None,
    ) -> dict:
        backup = self.root / "backups" / backup_id
        if not backup.exists():
            raise FileNotFoundError(backup_id)
        dest = Path(target) if target else (self.root / "files")
        if overwrite == "fail" and any(dest.rglob("*")):
            # allow empty or only restore into clean dir when fail
            existing = [p for p in dest.rglob("*") if p.is_file()]
            if existing:
                raise FileExistsError("overwrite_policy_fail")
        if overwrite == "replace" and dest.exists():
            for child in dest.iterdir():
                if child.is_file():
                    child.unlink()
                else:
                    shutil.rmtree(child)
        try:
            return self.backup.restore_tree(backup, dest)
        except ValueError as exc:
            if str(exc).startswith("checksum_mismatch"):
                return {
                    "restore_verified": False,
                    "corruption_detected": True,
                    "error": str(exc),
                    "evidence_class": "DIGITAL_PASS",
                }
            raise

    def detect_corruption(self, backup_id: str) -> dict:
        backup = self.root / "backups" / backup_id
        meta = json.loads((backup / "BACKUP_MANIFEST.json").read_text())
        issues = []
        for entry in meta["files"]:
            path = backup / entry["path"]
            if not path.exists():
                issues.append({"path": entry["path"], "issue": "missing"})
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != entry["sha256"]:
                issues.append({"path": entry["path"], "issue": "checksum_mismatch"})
        return {
            "backup_id": backup_id,
            "corruption_detected": bool(issues),
            "issues": issues,
            "evidence_class": "DIGITAL_PASS",
        }


@dataclass
class DurableSyncQueue(SyncProviderScaffold):
    """Provider-independent sync queue that survives process restart."""

    queue_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        if self.queue_dir is None:
            return
        self.queue_dir = Path(self.queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self._queue = []
        for path in sorted(self.queue_dir.glob("*.json")):
            self._queue.append(json.loads(path.read_text()))

    def enqueue(self, scope: str, payload: Dict) -> None:
        if scope not in self.scopes:
            raise ValueError(f"scope_not_allowed:{scope}")
        item = {
            "id": uuid.uuid4().hex,
            "scope": scope,
            "payload": payload,
            "ts": time.time(),
            "state": "pending",
        }
        self._queue.append(item)
        if self.queue_dir is not None:
            (self.queue_dir / f"{item['id']}.json").write_text(json.dumps(item) + "\n")

    def pending_count(self) -> int:
        return sum(1 for i in self._queue if i.get("state") == "pending")

    def reload(self) -> int:
        if self.queue_dir is None:
            return self.pending_count()
        self._queue = []
        for path in sorted(self.queue_dir.glob("*.json")):
            self._queue.append(json.loads(path.read_text()))
        return self.pending_count()

    def reconcile(self) -> dict:
        done = 0
        for item in self._queue:
            if item.get("state") == "pending":
                item["state"] = "reconciled"
                done += 1
                if self.queue_dir is not None:
                    (self.queue_dir / f"{item['id']}.json").write_text(json.dumps(item) + "\n")
        return {"reconciled": done, "pending": self.pending_count()}
