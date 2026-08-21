"""NET-ORCH-029 — durable checkpoint/resume with idempotency and A→B→C fresh-process proof."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import BearerClass, ContinuityState, ServiceSession

SCHEMA_VERSION = "wave006.checkpoint.v2"


def _integrity_payload(data: dict[str, Any]) -> str:
    clone = {k: v for k, v in data.items() if k != "integrity_hash"}
    blob = json.dumps(clone, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def create_session(
    *,
    session_id: str | None = None,
    service_id: str = "learning-session",
    bearer: str = "wifi-home",
    now: float = 1_700_000_000.0,
) -> ServiceSession:
    sid = session_id or f"sess-{uuid.uuid4().hex[:10]}"
    token = f"rtok-{uuid.uuid4().hex}"
    sess = ServiceSession(
        schema_version=SCHEMA_VERSION,
        checkpoint_id=f"ckpt-{uuid.uuid4().hex[:10]}",
        session_id=sid,
        service_id=service_id,
        logical_position=0,
        pending_operations=[],
        committed_operation_ids=[],
        idempotency_keys=[],
        resume_token=token,
        resume_token_expires_at=now + 3600.0,
        cache_references=[],
        bearer_before_failure=bearer,
        created_at=now,
        updated_at=now,
        resume_count=0,
        service_name=service_id,
        bearer=BearerClass.WIFI if "wifi" in bearer else BearerClass.CELLULAR,
        checkpoint={"progress": 0},
        sequence=0,
        continuity_state=ContinuityState.HEALTHY,
    )
    d = sess.to_dict()
    sess.integrity_hash = _integrity_payload(d)
    return sess


def mark_operation_committed(session: ServiceSession, op_id: str, *, now: float) -> ServiceSession:
    if op_id in session.committed_operation_ids:
        return session  # exactly-once
    session.committed_operation_ids.append(op_id)
    session.pending_operations = [op for op in session.pending_operations if op.get("op_id") != op_id]
    session.idempotency_keys.append(op_id)
    session.updated_at = now
    session.sequence += 1
    d = session.to_dict()
    session.integrity_hash = _integrity_payload(d)
    return session


def enqueue_operation(session: ServiceSession, op: dict[str, Any], *, now: float) -> ServiceSession:
    op_id = op["op_id"]
    if op_id in session.committed_operation_ids or any(p.get("op_id") == op_id for p in session.pending_operations):
        return session
    session.pending_operations.append(op)
    session.updated_at = now
    d = session.to_dict()
    session.integrity_hash = _integrity_payload(d)
    return session


def checkpoint(session: ServiceSession, path: Path, *, now: float | None = None) -> ServiceSession:
    if now is not None:
        session.updated_at = now
    d = session.to_dict()
    session.integrity_hash = _integrity_payload(d)
    d["integrity_hash"] = session.integrity_hash
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, sort_keys=True))
    os.replace(tmp, path)
    return session


save_session_checkpoint = checkpoint


def load_checkpoint(path: Path) -> ServiceSession:
    raw = json.loads(path.read_text())
    return _from_dict(raw)


load_session_checkpoint = load_checkpoint


def _from_dict(raw: dict[str, Any]) -> ServiceSession:
    bearer_raw = raw.get("bearer", "offline")
    try:
        bearer = BearerClass(bearer_raw)
    except Exception:
        bearer = BearerClass.OFFLINE
    state_raw = raw.get("continuity_state", ContinuityState.HEALTHY.value)
    try:
        state = ContinuityState(state_raw)
    except Exception:
        state = ContinuityState.HEALTHY
    return ServiceSession(
        schema_version=raw.get("schema_version", ""),
        checkpoint_id=raw.get("checkpoint_id", ""),
        session_id=raw.get("session_id", ""),
        service_id=raw.get("service_id", raw.get("service_name", "")),
        logical_position=int(raw.get("logical_position", raw.get("checkpoint", {}).get("progress", 0))),
        pending_operations=list(raw.get("pending_operations", [])),
        committed_operation_ids=list(raw.get("committed_operation_ids", [])),
        idempotency_keys=list(raw.get("idempotency_keys", [])),
        resume_token=raw.get("resume_token", ""),
        resume_token_expires_at=float(raw.get("resume_token_expires_at", 0)),
        cache_references=list(raw.get("cache_references", [])),
        bearer_before_failure=raw.get("bearer_before_failure", ""),
        created_at=float(raw.get("created_at", 0)),
        updated_at=float(raw.get("updated_at", 0)),
        resume_count=int(raw.get("resume_count", 0)),
        integrity_hash=raw.get("integrity_hash", ""),
        service_name=raw.get("service_name", raw.get("service_id", "")),
        bearer=bearer,
        checkpoint=dict(raw.get("checkpoint", {})),
        sequence=int(raw.get("sequence", 0)),
        continuity_state=state,
    )


def validate_checkpoint(session: ServiceSession, *, now: float, expected_token: str | None = None) -> dict[str, Any]:
    d = session.to_dict()
    expected = _integrity_payload(d)
    if session.schema_version != SCHEMA_VERSION:
        return {"ok": False, "reason": "unsupported_schema"}
    if session.integrity_hash != expected:
        return {"ok": False, "reason": "integrity_mismatch"}
    if now > session.resume_token_expires_at:
        return {"ok": False, "reason": "expired_resume_token"}
    if expected_token is not None and expected_token != session.resume_token:
        return {"ok": False, "reason": "wrong_session_token"}
    return {"ok": True}


def resume_once(
    session: ServiceSession,
    *,
    now: float,
    resume_token: str,
    apply_pending: bool = True,
) -> tuple[ServiceSession, dict[str, Any]]:
    v = validate_checkpoint(session, now=now, expected_token=resume_token)
    if not v["ok"]:
        return session, v

    # Duplicate resume after completion: idempotent no-op
    if session.resume_count > 0 and not session.pending_operations:
        return session, {"ok": True, "duplicate_resume": True, "applied": []}

    applied: list[str] = []
    if apply_pending:
        for op in list(session.pending_operations):
            op_id = op["op_id"]
            if op_id in session.committed_operation_ids:
                return session, {"ok": False, "reason": "committed_operation_replay", "op_id": op_id}
            session = mark_operation_committed(session, op_id, now=now)
            applied.append(op_id)

    session.resume_count += 1
    session.continuity_state = ContinuityState.RESUMING if session.resume_count == 1 else ContinuityState.HEALTHY
    session.updated_at = now
    session.checkpoint["progress"] = session.logical_position
    d = session.to_dict()
    session.integrity_hash = _integrity_payload(d)
    return session, {"ok": True, "duplicate_resume": False, "applied": applied}


def resume_session(session: ServiceSession, *, now: float | None = None) -> ServiceSession:
    """Legacy wrapper — uses stored token and does not silently reset."""
    now = session.updated_at if now is None else now
    sess, result = resume_once(session, now=now, resume_token=session.resume_token)
    if not result.get("ok"):
        raise ValueError(result.get("reason", "resume_failed"))
    return sess


def _subprocess_resume_script() -> str:
    return r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from gunnchos_device_os.service_continuity_execution.resume import (
    load_checkpoint, resume_once, checkpoint, mark_operation_committed, enqueue_operation
)
mode = sys.argv[2]
path = Path(sys.argv[3])
now = float(sys.argv[4])
token = sys.argv[5] if len(sys.argv) > 5 else None
sess = load_checkpoint(path)
if mode == "B":
    # Resume first (integrity), then record digital path switch without breaking ledger.
    sess, result = resume_once(sess, now=now, resume_token=token or sess.resume_token)
    assert result["ok"], result
    sess.bearer_before_failure = "cellular_generic"
    assert "op-1" in sess.committed_operation_ids
    assert "op-2" in sess.committed_operation_ids
    assert sess.committed_operation_ids.count("op-2") == 1
    assert sess.logical_position == 42
    assert result["applied"] == ["op-2"]
    checkpoint(sess, path, now=now)
    print(json.dumps({"mode":"B","committed":sess.committed_operation_ids,"progress":sess.logical_position,"resume_count":sess.resume_count}))
elif mode == "C":
    before = list(sess.committed_operation_ids)
    sess, result = resume_once(sess, now=now, resume_token=token or sess.resume_token)
    assert result["ok"], result
    assert result.get("duplicate_resume") is True or result.get("applied") == []
    assert sess.committed_operation_ids == before
    assert sess.committed_operation_ids.count("op-2") == 1
    assert sess.logical_position == 42
    print(json.dumps({"mode":"C","committed":sess.committed_operation_ids,"progress":sess.logical_position,"duplicate":True}))
else:
    raise SystemExit("bad mode")
"""


def prove_session_resume_a_b_c(storage_dir: Path) -> dict[str, Any]:
    storage_dir.mkdir(parents=True, exist_ok=True)
    ckpt = storage_dir / "session.json"
    now = 1_700_000_300.0

    # A: create, commit op-1, enqueue op-2, progress=42, persist, exit
    sess = create_session(session_id="sess-abc", service_id="learning", bearer="wifi-home", now=now)
    sess = mark_operation_committed(sess, "op-1", now=now)
    sess.logical_position = 42
    sess.checkpoint["progress"] = 42
    sess = enqueue_operation(sess, {"op_id": "op-2", "action": "apply_edit"}, now=now)
    token = sess.resume_token
    checkpoint(sess, ckpt, now=now)

    root = str(Path(__file__).resolve().parents[2])
    script = _subprocess_resume_script()

    # B: fresh OS process
    b = subprocess.run(
        [sys.executable, "-c", script, root, "B", str(ckpt), str(now + 10), token],
        capture_output=True,
        text=True,
        check=False,
    )
    # C: fresh OS process duplicate resume
    c = subprocess.run(
        [sys.executable, "-c", script, root, "C", str(ckpt), str(now + 20), token],
        capture_output=True,
        text=True,
        check=False,
    )

    # Failure modes in-process
    failures: dict[str, Any] = {}
    # malformed JSON
    bad = storage_dir / "bad.json"
    bad.write_text("{not-json")
    try:
        load_checkpoint(bad)
        failures["malformed_json"] = False
    except Exception:
        failures["malformed_json"] = True

    # integrity mismatch
    sess2 = load_checkpoint(ckpt)
    sess2.integrity_hash = "deadbeef"
    failures["integrity_mismatch"] = validate_checkpoint(sess2, now=now + 30)["reason"] == "integrity_mismatch"

    # unsupported schema
    sess3 = load_checkpoint(ckpt)
    sess3.schema_version = "ancient.v0"
    d = sess3.to_dict()
    sess3.integrity_hash = _integrity_payload(d)
    failures["unsupported_schema"] = validate_checkpoint(sess3, now=now + 30)["reason"] == "unsupported_schema"

    # expired token
    sess4 = load_checkpoint(ckpt)
    failures["expired_resume_token"] = (
        validate_checkpoint(sess4, now=sess4.resume_token_expires_at + 1)["reason"] == "expired_resume_token"
    )

    # wrong token
    failures["wrong_session_token"] = (
        validate_checkpoint(sess4, now=now + 30, expected_token="wrong")["reason"] == "wrong_session_token"
    )

    # committed operation replay
    sess5 = load_checkpoint(ckpt)
    sess5.pending_operations = [{"op_id": "op-1", "action": "replay"}]
    d = sess5.to_dict()
    sess5.integrity_hash = _integrity_payload(d)
    _, replay = resume_once(sess5, now=now + 40, resume_token=sess5.resume_token)
    failures["committed_operation_replay"] = replay.get("reason") == "committed_operation_replay"

    b_ok = b.returncode == 0
    c_ok = c.returncode == 0
    b_out = json.loads(b.stdout.strip().splitlines()[-1]) if b_ok and b.stdout.strip() else {"error": b.stderr}
    c_out = json.loads(c.stdout.strip().splitlines()[-1]) if c_ok and c.stdout.strip() else {"error": c.stderr}

    checks = {
        "process_b_ok": b_ok,
        "process_c_ok": c_ok,
        "op1_not_replayed": b_ok and b_out.get("committed", []).count("op-1") == 1,
        "op2_exactly_once": b_ok and b_out.get("committed", []).count("op-2") == 1,
        "progress_preserved": b_ok and b_out.get("progress") == 42 and c_ok and c_out.get("progress") == 42,
        "duplicate_resume_idempotent": c_ok and c_out.get("duplicate") is True,
        "failures": all(failures.values()),
    }
    ok = all(v if isinstance(v, bool) else all(v.values()) for v in checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.session_resume_a_b_c.v1",
        "ok": ok,
        "checks": checks,
        "process_a": {"committed": ["op-1"], "pending": ["op-2"], "progress": 42},
        "process_b": b_out,
        "process_c": c_out,
        "failures": failures,
        "SESSION_RESUME_EXACTLY_ONCE": bool(checks["op2_exactly_once"]),
        "SESSION_DUPLICATE_RESUME_BLOCKED": bool(checks["duplicate_resume_idempotent"]),
        "b_stderr": b.stderr[-500:] if not b_ok else "",
        "c_stderr": c.stderr[-500:] if not c_ok else "",
    }
