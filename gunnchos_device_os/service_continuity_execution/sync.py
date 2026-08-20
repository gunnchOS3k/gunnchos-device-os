"""NET-ORCH-034 — opportunistic synchronization (extends Wave004 persistent sync)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.platform.persistent_sync import (
    DeterministicPeerFixture,
    PersistentOfflineSyncEngine,
    run_a_b_c_restart_proof,
)
from gunnchos_device_os.service_continuity_execution.models import ContinuityState


def opportunistic_sync_when_healthy(
    engine: PersistentOfflineSyncEngine,
    peer: DeterministicPeerFixture,
    *,
    continuity_state: ContinuityState,
) -> dict[str, Any]:
    """Only flush pending ops when continuity is HEALTHY or DEGRADED (not FAILED/OFFLINE)."""
    if continuity_state in (ContinuityState.FAILED, ContinuityState.OFFLINE):
        return {
            "attempted": False,
            "reason": f"deferred_until_connectivity:{continuity_state.value}",
            "pending": len(engine.pending()),
            "remote_apply_count": peer.remote_apply_count,
        }
    flush = engine.flush_to_peer(peer)
    return {
        "attempted": True,
        "reason": "opportunistic_window",
        "pending": flush.get("pending_after_flush", len(engine.pending())),
        "remote_apply_count": flush.get("remote_apply_count", peer.remote_apply_count),
        "flush": flush,
    }


def prove_opportunistic_sync(storage_dir: Path) -> dict[str, Any]:
    storage_dir = Path(storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    # Reuse Wave004 A-B-C restart proof as base persistence evidence
    abc = run_a_b_c_restart_proof(storage_dir / "abc")

    # Opportunistic deferral when offline
    path = storage_dir / "opp"
    path.mkdir(parents=True, exist_ok=True)
    peer = DeterministicPeerFixture()
    eng = PersistentOfflineSyncEngine(storage_path=path, replica_id="wave006-opp")
    eng.put("k1", {"v": 1}, idempotency_key="OPP-1")
    deferred = opportunistic_sync_when_healthy(eng, peer, continuity_state=ContinuityState.OFFLINE)
    flushed = opportunistic_sync_when_healthy(eng, peer, continuity_state=ContinuityState.HEALTHY)

    # Fresh-process reload after opportunistic flush
    del eng
    eng2 = PersistentOfflineSyncEngine.from_storage(path)
    pending_after = len(eng2.pending())

    ok = (
        abc.get("ok") is True
        and deferred["attempted"] is False
        and deferred["pending"] == 1
        and flushed["attempted"] is True
        and flushed["remote_apply_count"] >= 1
        and pending_after == 0
    )
    return {
        "schema": "gunnchos.engineering_wave006.opportunistic_sync.v1",
        "ok": ok,
        "wave004_abc_reuse": {"ok": abc.get("ok"), "schema": abc.get("schema")},
        "deferred_while_offline": deferred,
        "flushed_when_healthy": {
            "attempted": flushed["attempted"],
            "remote_apply_count": flushed["remote_apply_count"],
            "pending": flushed["pending"],
        },
        "fresh_process_pending_after_flush": pending_after,
    }
