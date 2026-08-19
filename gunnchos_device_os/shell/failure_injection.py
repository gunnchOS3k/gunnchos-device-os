"""Failure injection helpers for Wave 002 tests (section 24)."""
from __future__ import annotations

from typing import Any


def inject_session_expiry(identity_store: Any, session_id: str) -> dict[str, Any]:
    sess = identity_store.service.sessions.get(session_id)
    if sess is None:
        return {"ok": False, "error": "unknown_session"}
    sess.expires_at_ms = 0
    identity_store.save()
    return {"ok": True, "session_id": session_id, "injected": "expiry"}


def inject_checkpoint_corruption(coordinator: Any, checkpoint_id: str) -> dict[str, Any]:
    meta = coordinator.checkpoints.get(checkpoint_id)
    if meta is None:
        return {"ok": False, "error": "unknown_checkpoint"}
    from pathlib import Path

    path = Path(meta["path"])
    path.write_text('{"corrupted": true}\n', encoding="utf-8")
    return {"ok": True, "checkpoint_id": checkpoint_id, "injected": "checksum_mismatch_expected"}


def inject_ring_replay(ring_service: Any) -> dict[str, Any]:
    ring_service.adapter.receiver.revocation.revoke_device("replay-ring")
    return {"ok": True, "injected": "revoked_ring_device"}
