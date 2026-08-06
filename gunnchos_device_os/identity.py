"""Local-only identity and checksum helpers for Gate 1 evidence."""
from __future__ import annotations

import hashlib
import json
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_device_id(prefix: str = "dev") -> str:
    """Stable-looking local device id (not a hardware serial)."""
    host = platform.node() or "local"
    digest = hashlib.sha256(f"{prefix}:{host}:{platform.machine()}".encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


def new_session_id(prefix: str = "sess") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def new_boot_id(prefix: str = "boot") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def new_dock_event_id(prefix: str = "dock") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_text(payload)


def stable_hardware_identity() -> dict[str, Any]:
    """Non-sensitive host identity fingerprint for evidence (no MAC/serial)."""
    machine = platform.machine() or "unknown"
    system = platform.system() or "unknown"
    release = platform.release() or "unknown"
    processor = platform.processor() or "unknown"
    raw = f"{system}|{machine}|{processor}|{release}"
    return {
        "platform": system,
        "arch": machine,
        "processor_class": processor or "unspecified",
        "kernel_release_class": release.split("-")[0] if release else "unknown",
        "identity_fingerprint": sha256_text(raw)[:16],
        "note": "Local fingerprint only; not a vendor serial or MAC.",
    }
