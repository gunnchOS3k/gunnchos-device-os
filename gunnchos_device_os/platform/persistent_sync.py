"""Persistent offline sync — store, queue, apply-once survive process restart."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.offline_sync import ConflictInfo, OfflineSyncEngine, SyncRecord, VectorClock

SCHEMA_VERSION = 1


class SyncStateError(ValueError):
    """Safe failure for corrupt or unsupported persisted sync state."""


def _record_from_dict(data: dict[str, Any]) -> SyncRecord:
    required = ("key", "replica_id", "wall_time_ms")
    for k in required:
        if k not in data:
            raise SyncStateError(f"corrupt_queue_record_missing_{k}")
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


def _state_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass
class DeterministicPeerFixture:
    """In-process peer/server fixture that counts remote applies."""

    applied: list[dict[str, Any]] = field(default_factory=list)
    by_op: dict[str, dict[str, Any]] = field(default_factory=dict)

    def apply(self, record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        if idempotency_key in self.by_op:
            return {"applied": False, "duplicate": True, "idempotency_key": idempotency_key}
        self.by_op[idempotency_key] = record
        self.applied.append({"idempotency_key": idempotency_key, "record": record})
        return {"applied": True, "duplicate": False, "idempotency_key": idempotency_key}

    @property
    def remote_apply_count(self) -> int:
        return len(self.applied)


@dataclass
class PersistentOfflineSyncEngine(OfflineSyncEngine):
    storage_path: Path | None = None
    schema_version: int = SCHEMA_VERSION
    idempotency_keys: set[str] = field(default_factory=set)
    pending_ops: list[dict[str, Any]] = field(default_factory=list)
    applied_ops: set[str] = field(default_factory=set)
    quarantined: list[dict[str, Any]] = field(default_factory=list)
    load_error: str | None = None

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
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self.load_error = "malformed_json"
            raise SyncStateError("malformed_json") from exc
        if not isinstance(data, dict):
            self.load_error = "corrupt_state_not_object"
            raise SyncStateError("corrupt_state_not_object")
        if data.get("schema_version", 0) != SCHEMA_VERSION:
            self.load_error = "unsupported_sync_schema_version"
            raise SyncStateError("unsupported_sync_schema_version")
        try:
            self.replica_id = data.get("replica_id", self.replica_id)
            self.store = {k: _record_from_dict(v) for k, v in data.get("store", {}).items()}
            self.queue = [_record_from_dict(r) for r in data.get("queue", [])]
            self.conflicts = [_conflict_from_dict(c) for c in data.get("conflicts", [])]
            self.idempotency_keys = set(data.get("idempotency_keys", []))
            self.pending_ops = list(data.get("pending_ops", []))
            self.applied_ops = set(data.get("applied_ops", []))
            self.quarantined = list(data.get("quarantined", []))
            # Rebuild pending_ops from queue if older state
            if not self.pending_ops and self.queue:
                for rec in self.queue:
                    self.pending_ops.append(
                        {
                            "idempotency_key": f"legacy:{rec.key}:{rec.version}",
                            "record": rec.to_dict(),
                        }
                    )
        except (KeyError, TypeError, ValueError, SyncStateError) as exc:
            self.load_error = "corrupt_queue_record"
            raise SyncStateError("corrupt_queue_record") from exc

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
            "pending_ops": list(self.pending_ops),
            "applied_ops": sorted(self.applied_ops),
            "quarantined": list(self.quarantined),
        }
        self._state_file().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def state_snapshot_hash(self) -> str:
        if self.storage_path is None or not self._state_file().exists():
            return _state_hash({"empty": True})
        data = json.loads(self._state_file().read_text(encoding="utf-8"))
        return _state_hash(data)

    def put(self, key: str, value: Any, *, idempotency_key: str | None = None) -> SyncRecord:
        if idempotency_key:
            if idempotency_key in self.idempotency_keys:
                existing = self.store.get(key)
                if existing:
                    return existing
            self.idempotency_keys.add(idempotency_key)
        record = super().put(key, value)
        if idempotency_key:
            self.pending_ops.append({"idempotency_key": idempotency_key, "record": record.to_dict()})
        else:
            auto_key = f"auto:{record.key}:{record.version}:{record.wall_time_ms}"
            self.pending_ops.append({"idempotency_key": auto_key, "record": record.to_dict()})
        self._persist()
        return record

    def delete(self, key: str) -> SyncRecord:
        record = super().delete(key)
        auto_key = f"del:{record.key}:{record.version}:{record.wall_time_ms}"
        self.pending_ops.append({"idempotency_key": auto_key, "record": record.to_dict()})
        self._persist()
        return record

    def apply_remote(self, remote_dict: dict[str, Any]) -> dict[str, Any]:
        result = super().apply_remote(remote_dict)
        self._persist()
        return result

    def sync_from_peer(self, peer_records: list[dict[str, Any]]) -> dict[str, Any]:
        result = super().sync_from_peer(peer_records)
        self.pending_ops.clear()
        self._persist()
        return result

    def clear_queue(self) -> None:
        super().clear_queue()
        self.pending_ops.clear()
        self._persist()

    def flush_to_peer(self, peer: DeterministicPeerFixture) -> dict[str, Any]:
        """Flush pending ops to peer with apply-once semantics."""
        applied_this_flush = 0
        skipped_duplicates = 0
        for op in list(self.pending_ops):
            idem = op["idempotency_key"]
            if idem in self.applied_ops:
                skipped_duplicates += 1
                continue
            peer.apply(op["record"], idempotency_key=idem)
            self.applied_ops.add(idem)
            applied_this_flush += 1
        self.queue.clear()
        self.pending_ops.clear()
        self._persist()
        return {
            "ok": True,
            "applied_this_flush": applied_this_flush,
            "skipped_duplicates": skipped_duplicates,
            "remote_apply_count": peer.remote_apply_count,
            "pending_after_flush": len(self.pending()),
        }

    def replay_pending_to_peer(self, peer: DeterministicPeerFixture) -> dict[str, Any]:
        """Replay previously applied ops — must not increase remote apply count."""
        before = peer.remote_apply_count
        replayed = 0
        for idem in sorted(self.applied_ops):
            # Re-present the op; peer dedupes
            peer.apply({"replay": True, "idempotency_key": idem}, idempotency_key=idem)
            replayed += 1
        after = peer.remote_apply_count
        return {
            "ok": after == before,
            "replayed": replayed,
            "remote_apply_count": after,
            "duplicate_suppressed": after == before,
        }

    @classmethod
    def from_storage(cls, storage_path: Path, *, replica_id: str | None = None) -> "PersistentOfflineSyncEngine":
        return cls(storage_path=storage_path, replica_id=replica_id or "replica-reload")

    @classmethod
    def try_from_storage(cls, storage_path: Path) -> dict[str, Any]:
        try:
            engine = cls.from_storage(storage_path)
            return {"ok": True, "engine": engine}
        except SyncStateError as exc:
            return {"ok": False, "error": str(exc)}


def run_a_b_c_restart_proof(storage_path: Path) -> dict[str, Any]:
    """Process A enqueue → B flush apply-once → C reload no duplicate."""
    storage_path = Path(storage_path)
    if storage_path.exists():
        for child in storage_path.glob("*"):
            if child.is_file():
                child.unlink()
    storage_path.mkdir(parents=True, exist_ok=True)
    peer = DeterministicPeerFixture()
    state_hashes: dict[str, str] = {}

    # Process A
    a = PersistentOfflineSyncEngine(storage_path=storage_path, replica_id="replica-abc")
    a.put("obj-1", {"n": 1}, idempotency_key="OP-001")
    process_a_pending = len(a.pending())
    state_hashes["after_a"] = a.state_snapshot_hash()
    replica_a = a.replica_id
    del a

    # Process B
    b = PersistentOfflineSyncEngine.from_storage(storage_path)
    process_b_loaded_pending = len(b.pending())
    replica_restored = b.replica_id == replica_a
    flush = b.flush_to_peer(peer)
    process_b_remote_apply_count = flush["remote_apply_count"]
    process_b_pending_after_flush = flush["pending_after_flush"]
    state_hashes["after_b"] = b.state_snapshot_hash()
    del b

    # Process C
    c = PersistentOfflineSyncEngine.from_storage(storage_path)
    process_c_pending = len(c.pending())
    replay = c.replay_pending_to_peer(peer)
    process_c_replay_remote_apply_count = replay["remote_apply_count"]
    state_hashes["after_c"] = c.state_snapshot_hash()
    value = c.get("obj-1")
    duplicate_suppressed = replay.get("duplicate_suppressed") is True

    ok = (
        process_a_pending == 1
        and process_b_loaded_pending == 1
        and replica_restored
        and process_b_remote_apply_count == 1
        and process_b_pending_after_flush == 0
        and process_c_pending == 0
        and process_c_replay_remote_apply_count == 1
        and duplicate_suppressed
        and value == {"n": 1}
    )
    return {
        "schema": "gunnchos.engineering_wave004.offline_sync_a_b_c_restart.v1",
        "process_a_pending": process_a_pending,
        "process_b_loaded_pending": process_b_loaded_pending,
        "process_b_remote_apply_count": process_b_remote_apply_count,
        "process_b_pending_after_flush": process_b_pending_after_flush,
        "process_c_pending": process_c_pending,
        "process_c_replay_remote_apply_count": process_c_replay_remote_apply_count,
        "duplicate_suppressed": duplicate_suppressed,
        "replica_restored": replica_restored,
        "state_hashes": state_hashes,
        "result": "PASS" if ok else "FAIL",
        "ok": ok,
    }


def prove_corruption_failures(storage_path: Path) -> dict[str, Any]:
    storage_path = Path(storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    state = storage_path / "sync_state.json"
    cases: dict[str, Any] = {}

    state.write_text("{not-json", encoding="utf-8")
    cases["malformed_json"] = PersistentOfflineSyncEngine.try_from_storage(storage_path)

    state.write_text(json.dumps({"schema_version": 99, "store": {}, "queue": []}), encoding="utf-8")
    cases["unsupported_schema"] = PersistentOfflineSyncEngine.try_from_storage(storage_path)

    state.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "replica_id": "x",
                "store": {},
                "queue": [{"key": "k"}],  # missing required fields
                "conflicts": [],
            }
        ),
        encoding="utf-8",
    )
    cases["corrupt_queue_record"] = PersistentOfflineSyncEngine.try_from_storage(storage_path)

    ok = all(v.get("ok") is False for v in cases.values())
    return {"ok": ok, "cases": cases}
