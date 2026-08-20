"""Persistent offline sync — store, queue, conflicts survive process restart."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.offline_sync import ConflictInfo, OfflineSyncEngine, SyncRecord, VectorClock

SCHEMA_VERSION = 1


def _record_from_dict(data: dict[str, Any]) -> SyncRecord:
    return SyncRecord(
        key=data["key"],
        value=data.get("value"),
        replica_id=data["replica_id"],
        wall_time_ms=int(data["wall_time_ms"]),
        vector=VectorClock.from_dict(data.get("vector")),
        version=int(data.get("version", 1)),
        tombstone=bool(data.get("tombstone", False)),
    )


def _conflict_from_dict(data: dict[str, Any]) -> ConflictInfo:
    return ConflictInfo(
        key=data["key"],
        local=data["local"],
        remote=data["remote"],
        policy=data["policy"],
        winner=data.get("winner"),
        reason=data["reason"],
    )


@dataclass
class PersistentOfflineSyncEngine(OfflineSyncEngine):
    storage_path: Path | None = None
    schema_version: int = SCHEMA_VERSION
    idempotency_keys: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.storage_path is not None:
            self.storage_path = Path(self.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._load()

    def _state_file(self) -> Path:
        assert self.storage_path is not None
        return self.storage_path / "sync_state.json"

    def _load(self) -> None:
        path = self._state_file()
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version", 0) != SCHEMA_VERSION:
            raise ValueError("unsupported_sync_schema_version")
        self.replica_id = data.get("replica_id", self.replica_id)
        self.store = {k: _record_from_dict(v) for k, v in data.get("store", {}).items()}
        self.queue = [_record_from_dict(r) for r in data.get("queue", [])]
        self.conflicts = [_conflict_from_dict(c) for c in data.get("conflicts", [])]
        self.idempotency_keys = set(data.get("idempotency_keys", []))

    def _persist(self) -> None:
        if self.storage_path is None:
            return
        payload = {
            "schema_version": SCHEMA_VERSION,
            "replica_id": self.replica_id,
            "policy": self.policy.value,
            "store": {k: v.to_dict() for k, v in self.store.items()},
            "queue": [r.to_dict() for r in self.queue],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "idempotency_keys": sorted(self.idempotency_keys),
        }
        self._state_file().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def put(self, key: str, value: Any, *, idempotency_key: str | None = None) -> SyncRecord:
        if idempotency_key:
            if idempotency_key in self.idempotency_keys:
                existing = self.store.get(key)
                if existing:
                    return existing
            self.idempotency_keys.add(idempotency_key)
        record = super().put(key, value)
        self._persist()
        return record

    def delete(self, key: str) -> SyncRecord:
        record = super().delete(key)
        self._persist()
        return record

    def apply_remote(self, remote_dict: dict[str, Any]) -> dict[str, Any]:
        result = super().apply_remote(remote_dict)
        self._persist()
        return result

    def sync_from_peer(self, peer_records: list[dict[str, Any]]) -> dict[str, Any]:
        result = super().sync_from_peer(peer_records)
        self._persist()
        return result

    def clear_queue(self) -> None:
        super().clear_queue()
        self._persist()

    @classmethod
    def from_storage(cls, storage_path: Path, *, replica_id: str | None = None) -> "PersistentOfflineSyncEngine":
        engine = cls(storage_path=storage_path, replica_id=replica_id or f"replica-reload")
        return engine
