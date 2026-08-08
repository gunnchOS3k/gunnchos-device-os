"""Shared persistence for the runnable DEV plane services.

Backends:
  - sqlite (default): real durable persistence with WAL for multi-instance
  - json: legacy file store for tiny local demos
  - memory: ephemeral (tests)

Redis is optional via REDIS_URL for cache/pubsub coordination in multi-instance
failure tests (falls back to in-process coordination when unavailable).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from gunnchos_device_os.cloud_dev_plane.claim import CLAIM_BOUNDARY, REALM
from gunnchos_device_os.identity import utc_now_iso

_EMPTY = {
    "identities": {},
    "enrollments": {},
    "sync_queue": [],
    "sync_delivered": [],
    "saves": {},
    "matchmaking": {},
    "telemetry": [],
    "update_metadata": {},
    "fleet": {},
    "diagnostics": [],
}


class DevPlaneStore:
    """Durable store shared by compose services or multi-instance tests."""

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        backend: str | None = None,
    ) -> None:
        self.path = Path(path) if path else None
        env_backend = None
        try:
            import os

            env_backend = os.environ.get("GUNNCHOS_STORE_BACKEND")
        except Exception:  # noqa: BLE001
            env_backend = None
        if backend:
            self.backend = backend.lower()
        elif env_backend:
            self.backend = env_backend.lower()
        elif self.path and str(self.path).endswith(".json"):
            self.backend = "json"
        elif self.path:
            self.backend = "sqlite"
        else:
            self.backend = "memory"

        if self.backend == "sqlite" and self.path and self.path.suffix == ".json":
            self.path = self.path.with_suffix(".sqlite3")
        if self.backend == "sqlite" and self.path is None:
            self.backend = "memory"

        self._lock = threading.RLock()
        self.data: dict[str, Any] = {
            **{k: ({} if isinstance(v, dict) else []) for k, v in _EMPTY.items()},
            "meta": {
                "realm": REALM,
                "claim_boundary": CLAIM_BOUNDARY,
                "backend": self.backend,
            },
        }
        self._redis = None
        self._init_backend()

    def _init_backend(self) -> None:
        if self.backend == "sqlite":
            assert self.path is not None
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(
                str(self.path),
                check_same_thread=False,
                isolation_level=None,
            )
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            self._load_sqlite()
        elif self.backend == "json":
            self._conn = None
            if self.path and self.path.exists():
                self._load_json()
        else:
            self._conn = None

        # Optional Redis coordination (best-effort).
        try:
            import os

            redis_url = os.environ.get("GUNNCHOS_REDIS_URL") or os.environ.get("REDIS_URL")
            if redis_url:
                try:
                    import redis  # type: ignore

                    self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
                    self._redis.ping()
                except Exception:  # noqa: BLE001
                    self._redis = None
        except Exception:  # noqa: BLE001
            self._redis = None

    def _load_json(self) -> None:
        assert self.path is not None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.data.update(raw)
        self.data.setdefault("meta", {})
        self.data["meta"]["backend"] = "json"

    def _load_sqlite(self) -> None:
        assert self._conn is not None
        row = self._conn.execute("SELECT value FROM kv WHERE key = ?", ("root",)).fetchone()
        if not row:
            self.persist()
            return
        raw = json.loads(row[0])
        self.data.update(raw)
        self.data.setdefault("meta", {})
        self.data["meta"]["backend"] = "sqlite"

    def persist(self) -> None:
        with self._lock:
            self.data.setdefault("meta", {})
            self.data["meta"]["backend"] = self.backend
            self.data["meta"]["realm"] = REALM
            self.data["meta"]["claim_boundary"] = CLAIM_BOUNDARY
            self.data["meta"]["updated_at"] = utc_now_iso()
            if self.backend == "sqlite":
                assert self._conn is not None
                self._conn.execute("BEGIN IMMEDIATE")
                try:
                    row = self._conn.execute(
                        "SELECT value FROM kv WHERE key = ?", ("root",)
                    ).fetchone()
                    if row:
                        existing = json.loads(row[0])
                        self.data = self._merge_docs(existing, self.data)
                    payload = json.dumps(self.data, sort_keys=True, default=str)
                    self._conn.execute(
                        "INSERT INTO kv(key, value) VALUES(?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        ("root", payload),
                    )
                    self._conn.execute("COMMIT")
                except Exception:
                    self._conn.execute("ROLLBACK")
                    raise
            elif self.backend == "json" and self.path is not None:
                payload_obj = self.data
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps(payload_obj, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                tmp.replace(self.path)
            if self._redis is not None:
                try:
                    payload = json.dumps(self.data, sort_keys=True, default=str)
                    self._redis.set("gunnchos:dev_plane:root", payload)
                    self._redis.publish("gunnchos:dev_plane:events", "persist")
                except Exception:  # noqa: BLE001
                    pass

    @staticmethod
    def _merge_docs(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        """Merge durable docs for multi-instance writers (dict union / list extend)."""
        out = dict(base)
        dict_keys = (
            "identities",
            "enrollments",
            "saves",
            "matchmaking",
            "update_metadata",
            "fleet",
        )
        list_keys = ("sync_queue", "sync_delivered", "telemetry", "diagnostics")
        for key in dict_keys:
            merged = dict(out.get(key) or {})
            merged.update(dict(incoming.get(key) or {}))
            out[key] = merged
        for key in list_keys:
            left = list(out.get(key) or [])
            right = list(incoming.get(key) or [])
            # Prefer union by JSON fingerprint to limit duplicates under concurrency.
            seen = {json.dumps(item, sort_keys=True, default=str) for item in left}
            for item in right:
                fp = json.dumps(item, sort_keys=True, default=str)
                if fp not in seen:
                    left.append(item)
                    seen.add(fp)
            out[key] = left
        meta = dict(out.get("meta") or {})
        meta.update(dict(incoming.get("meta") or {}))
        out["meta"] = meta
        return out
    def reload(self) -> None:
        """Reload from durable backend (multi-instance coherence)."""
        with self._lock:
            if self.backend == "sqlite":
                self._load_sqlite()
            elif self.backend == "json" and self.path and self.path.exists():
                self._load_json()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            if self.backend == "sqlite":
                # Pull latest committed state for multi-instance readers.
                self._load_sqlite()
            return {
                "identity_count": len(self.data["identities"]),
                "enrollment_count": len(self.data["enrollments"]),
                "sync_queue_depth": len(self.data["sync_queue"]),
                "sync_delivered_count": len(self.data["sync_delivered"]),
                "saves_count": len(self.data["saves"]),
                "matchmaking_count": len(self.data["matchmaking"]),
                "telemetry_buffered": len(self.data["telemetry"]),
                "update_channels": sorted(self.data["update_metadata"].keys()),
                "fleet_devices": sorted(self.data["fleet"].keys()),
                "diagnostics_count": len(self.data["diagnostics"]),
                "backend": self.backend,
                "redis_attached": bool(self._redis),
                "realm": REALM,
                "claim_boundary": CLAIM_BOUNDARY,
                "updated_at": utc_now_iso(),
                "mock": False,
            }

    def close(self) -> None:
        with self._lock:
            if getattr(self, "_conn", None) is not None:
                self._conn.close()
                self._conn = None
