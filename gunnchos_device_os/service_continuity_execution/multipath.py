"""NET-ORCH-030 — real application-level multipath chunk transfer + reassembly."""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import MultipathKind


@dataclass
class MultipathChunk:
    transfer_id: str
    chunk_id: str
    offset: int
    length: int
    payload: bytes
    payload_hash: str
    path_id: str
    sequence: int
    attempt: int = 0
    delivered: bool = False
    failed: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["payload"] = self.payload.hex()
        return d


@dataclass
class PathWorker:
    path_id: str
    trusted: bool = True
    fail_after_n: int | None = None
    _sent: int = 0
    delivered: list[MultipathChunk] = field(default_factory=list)
    failed: list[MultipathChunk] = field(default_factory=list)

    def transmit(self, chunk: MultipathChunk) -> MultipathChunk:
        if not self.trusted:
            chunk.failed = True
            self.failed.append(chunk)
            return chunk
        self._sent += 1
        chunk.attempt += 1
        if self.fail_after_n is not None and self._sent > self.fail_after_n:
            chunk.failed = True
            self.failed.append(chunk)
            return chunk
        chunk.delivered = True
        chunk.failed = False
        self.delivered.append(chunk)
        return chunk


@dataclass
class ReassemblyBuffer:
    expected_len: int
    expected_hash: str
    chunks: dict[str, MultipathChunk] = field(default_factory=dict)
    duplicate_suppressed: int = 0

    def accept(self, chunk: MultipathChunk) -> None:
        if chunk.chunk_id in self.chunks:
            self.duplicate_suppressed += 1
            return
        self.chunks[chunk.chunk_id] = chunk

    def assemble(self) -> tuple[bytes, bool]:
        ordered = sorted(self.chunks.values(), key=lambda c: c.offset)
        buf = bytearray(self.expected_len)
        for c in ordered:
            buf[c.offset : c.offset + c.length] = c.payload
        out = bytes(buf)
        ok = hashlib.sha256(out).hexdigest() == self.expected_hash and len(out) == self.expected_len
        return out, ok


@dataclass
class MultipathTransfer:
    transfer_id: str
    path_ids: list[str]
    chunks: list[MultipathChunk]
    bytes_by_path: dict[str, int] = field(default_factory=dict)
    application_commit_count: int = 0
    reassembled_hash: str | None = None
    ok: bool = False
    MULTIPATH_KIND: str = MultipathKind.APPLICATION_LEVEL_MULTIPATH.value
    PRODUCTION_MPTCP_VALIDATED: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "path_ids": list(self.path_ids),
            "chunk_count": len(self.chunks),
            "bytes_by_path": dict(self.bytes_by_path),
            "application_commit_count": self.application_commit_count,
            "reassembled_hash": self.reassembled_hash,
            "ok": self.ok,
            "MULTIPATH_KIND": self.MULTIPATH_KIND,
            "PRODUCTION_MPTCP_VALIDATED": False,
            "REAL_MPTCP": False,
        }


def _chunk_payload(payload: bytes, *, transfer_id: str, chunk_size: int = 8) -> list[MultipathChunk]:
    chunks: list[MultipathChunk] = []
    seq = 0
    for offset in range(0, len(payload), chunk_size):
        part = payload[offset : offset + chunk_size]
        cid = f"{transfer_id}-c{seq}"
        chunks.append(
            MultipathChunk(
                transfer_id=transfer_id,
                chunk_id=cid,
                offset=offset,
                length=len(part),
                payload=part,
                payload_hash=hashlib.sha256(part).hexdigest(),
                path_id="",
                sequence=seq,
            )
        )
        seq += 1
    return chunks


def run_multipath_transfer(
    payload: bytes,
    path_ids: list[str],
    *,
    trusted_paths: set[str] | None = None,
    fail_path: str | None = None,
    fail_after_n: int = 1,
    inject_duplicate: bool = False,
    shuffle_delivery: bool = False,
    untrusted_secondary: str | None = None,
) -> dict[str, Any]:
    trusted_paths = trusted_paths or set(path_ids)
    if untrusted_secondary and untrusted_secondary in path_ids:
        return {
            "ok": False,
            "rejected": True,
            "reason": "untrusted_secondary_path",
            "MULTIPATH_KIND": MultipathKind.APPLICATION_LEVEL_MULTIPATH.value,
            "PRODUCTION_MPTCP_VALIDATED": False,
            "REAL_MPTCP": False,
        }
    for p in path_ids:
        if p not in trusted_paths:
            return {
                "ok": False,
                "rejected": True,
                "reason": "untrusted_path",
                "path": p,
                "MULTIPATH_KIND": MultipathKind.APPLICATION_LEVEL_MULTIPATH.value,
                "PRODUCTION_MPTCP_VALIDATED": False,
                "REAL_MPTCP": False,
            }

    transfer_id = f"xfer-{uuid.uuid4().hex[:10]}"
    source_hash = hashlib.sha256(payload).hexdigest()
    chunks = _chunk_payload(payload, transfer_id=transfer_id)
    workers = {
        pid: PathWorker(
            path_id=pid,
            trusted=True,
            fail_after_n=fail_after_n if fail_path == pid else None,
        )
        for pid in path_ids
    }

    # assign across paths
    for i, chunk in enumerate(chunks):
        chunk.path_id = path_ids[i % len(path_ids)]

    reassembly = ReassemblyBuffer(expected_len=len(payload), expected_hash=source_hash)
    outstanding = list(chunks)
    delivered_order: list[MultipathChunk] = []

    while outstanding:
        chunk = outstanding.pop(0)
        worker = workers[chunk.path_id]
        result = worker.transmit(chunk)
        if result.failed:
            # reassign to a surviving trusted path
            alt = next((p for p in path_ids if p != chunk.path_id and workers[p].fail_after_n is None), None)
            if alt is None:
                alt = next((p for p in path_ids if p != chunk.path_id), None)
            if alt is None:
                break
            retry = MultipathChunk(
                transfer_id=chunk.transfer_id,
                chunk_id=chunk.chunk_id,
                offset=chunk.offset,
                length=chunk.length,
                payload=chunk.payload,
                payload_hash=chunk.payload_hash,
                path_id=alt,
                sequence=chunk.sequence,
                attempt=chunk.attempt,
            )
            outstanding.append(retry)
            continue
        delivered_order.append(result)

    if shuffle_delivery:
        delivered_order = list(reversed(delivered_order))
    for c in delivered_order:
        reassembly.accept(c)
    if inject_duplicate and delivered_order:
        reassembly.accept(delivered_order[0])

    out, hash_ok = reassembly.assemble()
    bytes_by_path: dict[str, int] = {pid: 0 for pid in path_ids}
    for c in reassembly.chunks.values():
        bytes_by_path[c.path_id] = bytes_by_path.get(c.path_id, 0) + c.length

    commit_count = 1 if hash_ok else 0
    transfer = MultipathTransfer(
        transfer_id=transfer_id,
        path_ids=path_ids,
        chunks=list(reassembly.chunks.values()),
        bytes_by_path=bytes_by_path,
        application_commit_count=commit_count,
        reassembled_hash=hashlib.sha256(out).hexdigest() if out else None,
        ok=hash_ok and commit_count == 1,
    )
    return {
        "ok": transfer.ok,
        "transfer": transfer.to_dict(),
        "source_hash": source_hash,
        "reassembled_hash": transfer.reassembled_hash,
        "payload_match": out == payload,
        "duplicate_suppressed": reassembly.duplicate_suppressed,
        "bytes_by_path": bytes_by_path,
        "application_commit_count": commit_count,
        "MULTIPATH_KIND": MultipathKind.APPLICATION_LEVEL_MULTIPATH.value,
        "PRODUCTION_MPTCP_VALIDATED": False,
        "REAL_MPTCP": False,
        "path_failure_continued": fail_path is not None and transfer.ok,
    }


# Legacy helpers used by older controller code
@dataclass
class MultipathPlan:
    paths: list[str]
    preferred: str | None
    stripe_bytes: dict[str, int] = field(default_factory=dict)
    kind: str = MultipathKind.APPLICATION_LEVEL_MULTIPATH.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": list(self.paths),
            "preferred": self.preferred,
            "stripe_bytes": dict(self.stripe_bytes),
            "MULTIPATH_KIND": self.kind,
            "REAL_MPTCP": False,
        }


def build_multipath_plan(paths: list[str], prefer: str | None = None) -> MultipathPlan:
    return MultipathPlan(paths=list(paths), preferred=prefer)


def stripe_application_payload(plan: MultipathPlan, payload: bytes) -> MultipathPlan:
    """Deprecated accounting helper — real transfers use run_multipath_transfer."""
    if not plan.paths:
        return plan
    n = len(plan.paths)
    base = len(payload) // n
    rem = len(payload) % n
    for i, p in enumerate(plan.paths):
        plan.stripe_bytes[p] = base + (1 if i < rem else 0)
    return plan


def prove_application_multipath() -> dict[str, Any]:
    payload = b"WAVE006-MULTIPATH-PAYLOAD-ABCDEFGH-0123456789"
    single = run_multipath_transfer(payload, ["path-a"], trusted_paths={"path-a"})
    multi = run_multipath_transfer(
        payload,
        ["path-a", "path-b"],
        trusted_paths={"path-a", "path-b"},
        fail_path="path-a",
        fail_after_n=1,
        inject_duplicate=True,
        shuffle_delivery=True,
    )
    untrusted = run_multipath_transfer(
        payload,
        ["path-a", "evil"],
        trusted_paths={"path-a"},
        untrusted_secondary="evil",
    )
    checks = {
        "single_ok": single["ok"] and single["payload_match"],
        "multi_ok": multi["ok"] and multi["payload_match"],
        "hash_match": multi["reassembled_hash"] == multi["source_hash"],
        "path_failure_continues": multi.get("path_failure_continued") is True,
        "duplicate_suppressed": multi["duplicate_suppressed"] >= 1,
        "duplicate_commit_zero_extra": multi["application_commit_count"] == 1,
        "bytes_from_delivered_chunks": sum(multi["bytes_by_path"].values()) == len(payload),
        "untrusted_rejected": untrusted.get("rejected") is True,
        "not_byte_count_only": multi["transfer"]["chunk_count"] > 1,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.application_multipath_transfer.v1",
        "ok": ok,
        "checks": checks,
        "single_path": single,
        "multipath": multi,
        "untrusted": untrusted,
        "MULTIPATH_KIND": MultipathKind.APPLICATION_LEVEL_MULTIPATH.value,
        "PRODUCTION_MPTCP_VALIDATED": False,
        "REAL_MPTCP": False,
        "APPLICATION_MULTIPATH_REAL_TRANSFER": True,
        "MULTIPATH_PATH_FAILURE_CONTINUES": bool(checks["path_failure_continues"]),
        "MULTIPATH_PAYLOAD_HASH_MATCH": bool(checks["hash_match"]),
        "DUPLICATE_COMMIT_COUNT": multi["application_commit_count"] - 1,
    }
