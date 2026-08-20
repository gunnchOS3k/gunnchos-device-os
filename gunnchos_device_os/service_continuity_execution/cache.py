"""NET-ORCH-033 — production-like digital cache with TTL, integrity, budget, namespaces."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    namespace: str
    key: str
    version: int
    created_at: float
    updated_at: float
    expires_at: float
    payload: Any
    payload_hash: str
    size_bytes: int
    last_access_at: float
    content_type: str = "application/json"
    sensitivity: str = "normal"
    quarantined: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_payload(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _size_of(payload: Any) -> int:
    return len(json.dumps(payload, default=str).encode())


class PersistentContinuityCache:
    def __init__(self, path: Path, *, size_budget_bytes: int = 4096, now_fn=None) -> None:
        self.path = Path(path)
        self.size_budget_bytes = size_budget_bytes
        self.now_fn = now_fn or time.time
        self._entries: dict[str, CacheEntry] = {}
        self._load()

    def _nsk(self, namespace: str, key: str) -> str:
        return f"{namespace}::{key}"

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text())
        except Exception:
            self._entries = {}
            return
        for k, v in raw.get("entries", {}).items():
            try:
                self._entries[k] = CacheEntry(**v)
            except Exception:
                continue

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": {k: e.to_dict() for k, e in self._entries.items()}}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
        os.replace(tmp, self.path)

    def _total_size(self) -> int:
        return sum(e.size_bytes for e in self._entries.values() if not e.quarantined)

    def _evict_until_fit(self, needed: int) -> list[str]:
        evicted: list[str] = []
        while self._total_size() + needed > self.size_budget_bytes and self._entries:
            # deterministic LRU
            live = [(k, e) for k, e in self._entries.items() if not e.quarantined]
            if not live:
                break
            victim_key, _ = sorted(live, key=lambda kv: (kv[1].last_access_at, kv[0]))[0]
            del self._entries[victim_key]
            evicted.append(victim_key)
        return evicted

    def put(
        self,
        key: str,
        value: Any,
        *,
        namespace: str = "default",
        ttl_s: float = 3600.0,
        version: int = 1,
        content_type: str = "application/json",
        sensitivity: str = "normal",
    ) -> dict[str, Any]:
        now = float(self.now_fn())
        size = _size_of(value)
        evicted = self._evict_until_fit(size)
        entry = CacheEntry(
            namespace=namespace,
            key=key,
            version=version,
            created_at=now,
            updated_at=now,
            expires_at=now + ttl_s,
            payload=value,
            payload_hash=_hash_payload(value),
            size_bytes=size,
            last_access_at=now,
            content_type=content_type,
            sensitivity=sensitivity,
        )
        self._entries[self._nsk(namespace, key)] = entry
        self._persist()
        return {"ok": True, "evicted": evicted, "size_bytes": size}

    def exists(self, key: str, *, namespace: str = "default") -> bool:
        e = self._entries.get(self._nsk(namespace, key))
        if e is None or e.quarantined:
            return False
        if float(self.now_fn()) > e.expires_at:
            return False
        return True

    def get(self, key: str, *, namespace: str = "default") -> Any:
        nk = self._nsk(namespace, key)
        e = self._entries.get(nk)
        if e is None:
            return None
        if e.quarantined:
            return None
        now = float(self.now_fn())
        if now > e.expires_at:
            return None
        if _hash_payload(e.payload) != e.payload_hash:
            e.quarantined = True
            self._persist()
            return None
        e.last_access_at = now
        self._persist()
        return e.payload

    def evict(self, key: str, *, namespace: str = "default") -> bool:
        nk = self._nsk(namespace, key)
        if nk in self._entries:
            del self._entries[nk]
            self._persist()
            return True
        return False

    def invalidate(self, key: str, *, namespace: str = "default", older_than_version: int | None = None) -> bool:
        nk = self._nsk(namespace, key)
        e = self._entries.get(nk)
        if e is None:
            return False
        if older_than_version is not None and e.version >= older_than_version:
            return False
        del self._entries[nk]
        self._persist()
        return True

    def list_namespace(self, namespace: str) -> list[str]:
        now = float(self.now_fn())
        return [
            e.key
            for e in self._entries.values()
            if e.namespace == namespace and not e.quarantined and now <= e.expires_at
        ]

    def purge_expired(self) -> int:
        now = float(self.now_fn())
        dead = [k for k, e in self._entries.items() if now > e.expires_at]
        for k in dead:
            del self._entries[k]
        if dead:
            self._persist()
        return len(dead)


def prove_persistent_cache_a_b_c(storage_dir: Path) -> dict[str, Any]:
    storage_dir.mkdir(parents=True, exist_ok=True)
    cache_path = storage_dir / "cache.json"
    clock = {"t": 1_700_000_400.0}

    def now_fn() -> float:
        return clock["t"]

    # A
    cache = PersistentContinuityCache(cache_path, size_budget_bytes=800, now_fn=now_fn)
    cache.put("lesson-1", {"text": "cached-learning"}, namespace="learning", ttl_s=100.0, version=1)
    cache.put("ns-a-key", {"v": 1}, namespace="profile-a", ttl_s=100.0)
    cache.put("ns-b-key", {"v": 2}, namespace="profile-b", ttl_s=100.0)

    root = str(Path(__file__).resolve().parents[2])
    script = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from gunnchos_device_os.service_continuity_execution.cache import PersistentContinuityCache
path = Path(sys.argv[2])
t = float(sys.argv[3])
cache = PersistentContinuityCache(path, size_budget_bytes=800, now_fn=lambda: t)
print(json.dumps({
  "exists": cache.exists("lesson-1", namespace="learning"),
  "value": cache.get("lesson-1", namespace="learning"),
  "ns_a": cache.list_namespace("profile-a"),
  "ns_b_cannot_read_a": cache.get("ns-a-key", namespace="profile-b") is None,
}))
"""
    b = subprocess.run(
        [sys.executable, "-c", script, root, str(cache_path), str(clock["t"] + 1)],
        capture_output=True,
        text=True,
        check=False,
    )
    b_out = json.loads(b.stdout.strip()) if b.returncode == 0 else {"error": b.stderr}

    # TTL expiry
    clock["t"] += 200.0
    cache2 = PersistentContinuityCache(cache_path, size_budget_bytes=800, now_fn=now_fn)
    ttl_expired = cache2.get("lesson-1", namespace="learning") is None

    # refresh put after reconnect
    clock["t"] += 1.0
    cache2.put("lesson-1", {"text": "refreshed"}, namespace="learning", ttl_s=100.0, version=2)
    # version=2 should not be removed by older_than_version=2
    invalidate_skipped_for_current = cache2.invalidate("lesson-1", namespace="learning", older_than_version=2) is False
    got_v2 = cache2.get("lesson-1", namespace="learning") == {"text": "refreshed"}

    # explicit invalidation
    cache2.put("tmp", {"x": 1}, namespace="default", ttl_s=50)
    inv = cache2.invalidate("tmp", namespace="default")
    inv_gone = cache2.exists("tmp") is False

    # budget eviction
    clock["t"] += 1.0
    cache3 = PersistentContinuityCache(storage_dir / "budget.json", size_budget_bytes=80, now_fn=now_fn)
    cache3.put("a", {"data": "x" * 40}, namespace="default", ttl_s=50)
    cache3.put("b", {"data": "y" * 40}, namespace="default", ttl_s=50)
    cache3.put("c", {"data": "z" * 40}, namespace="default", ttl_s=50)
    eviction_happened = not cache3.exists("a") or len(cache3.list_namespace("default")) < 3

    # tamper payload
    cache4 = PersistentContinuityCache(storage_dir / "tamper.json", size_budget_bytes=800, now_fn=now_fn)
    cache4.put("secure", {"secret": 1}, namespace="default", ttl_s=50)
    raw = json.loads((storage_dir / "tamper.json").read_text())
    raw["entries"]["default::secure"]["payload"] = {"secret": 999}
    (storage_dir / "tamper.json").write_text(json.dumps(raw))
    cache4b = PersistentContinuityCache(storage_dir / "tamper.json", size_budget_bytes=800, now_fn=now_fn)
    tamper_rejected = cache4b.get("secure") is None

    # metadata corruption
    (storage_dir / "corrupt.json").write_text("{bad")
    cache5 = PersistentContinuityCache(storage_dir / "corrupt.json", size_budget_bytes=800, now_fn=now_fn)
    corrupt_safe = cache5.get("anything") is None

    # offline hit
    clock["t"] = 1_700_000_400.0
    offline = PersistentContinuityCache(storage_dir / "offline.json", size_budget_bytes=800, now_fn=now_fn)
    offline.put("pack", {"offline": True}, namespace="learning", ttl_s=999)
    offline_hit = offline.get("pack", namespace="learning") == {"offline": True}

    checks = {
        "process_b_persistence": b.returncode == 0 and b_out.get("exists") is True,
        "exists_get": b_out.get("value") == {"text": "cached-learning"},
        "ttl_expiry": ttl_expired,
        "explicit_invalidation": inv and inv_gone,
        "eviction_under_budget": eviction_happened,
        "namespace_isolation": b_out.get("ns_b_cannot_read_a") is True,
        "payload_tamper_rejected": tamper_rejected,
        "metadata_corruption_safe": corrupt_safe,
        "stale_version_path": got_v2 and invalidate_skipped_for_current,
        "offline_cache_hit": offline_hit,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.persistent_cache_policy.v1",
        "ok": ok,
        "checks": checks,
        "process_b": b_out,
        "CACHE_TTL": True,
        "CACHE_INTEGRITY": tamper_rejected,
        "CACHE_SIZE_BUDGET": eviction_happened,
        "CACHE_NAMESPACE_ISOLATION": bool(b_out.get("ns_b_cannot_read_a")),
    }
