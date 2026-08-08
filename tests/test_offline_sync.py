"""Offline sync — LWW and vector-clock conflict policies."""
from __future__ import annotations

from gunnchos_device_os.offline_mode_manager import create_sync_engine, enable_offline_mode, get_offline_plan
from gunnchos_device_os.offline_sync import ConflictPolicy, OfflineSyncEngine, VectorClock


def test_offline_plan_is_not_placeholder():
    plan = get_offline_plan()
    assert plan["mock"] is False
    assert plan["conflict_handling"] != "placeholder_last_write_wins"
    assert ConflictPolicy.VECTOR_CLOCK.value in plan["conflict_policies_available"]


def test_enable_offline_mode_returns_real_engine_snapshot():
    enabled = enable_offline_mode("camp", policy=ConflictPolicy.LWW)
    assert enabled["mock"] is False
    assert enabled["sync_engine"]["policy"] == ConflictPolicy.LWW.value
    assert enabled["plan"]["conflict_handling"] == ConflictPolicy.LWW.value


def test_vector_clock_happens_before():
    a = VectorClock({"r1": 1})
    b = VectorClock({"r1": 2})
    assert a.happens_before(b)
    assert not b.happens_before(a)
    c = VectorClock({"r1": 1, "r2": 1})
    d = VectorClock({"r1": 2})
    assert c.concurrent_with(d)


def test_causal_remote_wins_under_vector_clock():
    local = OfflineSyncEngine(replica_id="A", policy=ConflictPolicy.VECTOR_CLOCK, now_ms=lambda: 1000)
    local.put("note", "v1")
    remote_rec = local.pending()[0]
    # Peer B advances causally from A's version
    remote_rec = {
        **remote_rec,
        "replica_id": "B",
        "value": "v2",
        "wall_time_ms": 2000,
        "vector": {"A": 1, "B": 1},
        "version": 2,
    }
    peer = OfflineSyncEngine(replica_id="B", policy=ConflictPolicy.VECTOR_CLOCK, now_ms=lambda: 2000)
    # Seed peer store empty; apply to local
    result = local.apply_remote(remote_rec)
    assert result["status"] == "synced"
    assert local.get("note") == "v2"
    assert result["mock"] is False


def test_concurrent_vector_clock_marks_conflict_and_merges():
    a = OfflineSyncEngine(replica_id="A", policy=ConflictPolicy.VECTOR_CLOCK, now_ms=lambda: 1000)
    a.put("doc", "from-A")
    # Concurrent edit from B with divergent clock
    remote = {
        "key": "doc",
        "value": "from-B",
        "replica_id": "B",
        "wall_time_ms": 1500,
        "vector": {"B": 1},
        "version": 1,
    }
    result = a.apply_remote(remote)
    assert result["status"] == "conflict"
    assert result["conflict"]["winner"] == "merged_lww_fallback"
    assert a.get("doc") == "from-B"  # remote newer wall clock
    assert "A" in a.store["doc"].vector.clocks
    assert "B" in a.store["doc"].vector.clocks


def test_lww_prefers_newer_wall_time():
    engine = OfflineSyncEngine(replica_id="A", policy=ConflictPolicy.LWW, now_ms=lambda: 1000)
    engine.put("k", "old")
    remote = {
        "key": "k",
        "value": "new",
        "replica_id": "B",
        "wall_time_ms": 5000,
        "vector": {"B": 1},
        "version": 1,
    }
    result = engine.apply_remote(remote)
    assert result["status"] == "resolved"
    assert engine.get("k") == "new"
    assert result["conflict"]["winner"] == "remote"


def test_lww_tie_break_replica_id():
    engine = OfflineSyncEngine(replica_id="A", policy=ConflictPolicy.LWW, now_ms=lambda: 1000)
    engine.put("k", "from-A")
    remote = {
        "key": "k",
        "value": "from-Z",
        "replica_id": "Z",
        "wall_time_ms": 1000,
        "vector": {"Z": 1},
        "version": 1,
    }
    result = engine.apply_remote(remote)
    assert result["conflict"]["reason"] == "tie_break_replica_id"
    assert engine.get("k") == "from-Z"


def test_sync_from_peer_clears_queue():
    a = create_sync_engine(replica_id="A", policy=ConflictPolicy.VECTOR_CLOCK)
    # Freeze time via direct engine
    a.now_ms = lambda: 10
    a.put("x", 1)
    assert len(a.pending()) == 1
    b = OfflineSyncEngine(replica_id="B", policy=ConflictPolicy.VECTOR_CLOCK, now_ms=lambda: 20)
    b.put("y", 2)
    out = a.sync_from_peer(b.pending())
    assert out["mock"] is False
    assert a.get("y") == 2
    assert a.pending() == []


def test_delete_tombstone():
    eng = OfflineSyncEngine(replica_id="A", now_ms=lambda: 1)
    eng.put("gone", "x")
    eng.delete("gone")
    assert eng.get("gone") is None
    assert eng.store["gone"].tombstone is True
