"""DEV-realm HMAC signing for Stage 2 images/updates (not production keys)."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

DEV_REALM = "gunnchos-stage2-dev-signing-v1"
# Deterministic DEV secret — rejected for any PROD claim.
_DEV_SECRET = hashlib.sha256(f"{DEV_REALM}:not-production".encode()).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sign_payload(payload: dict[str, Any]) -> str:
    body = {
        k: v
        for k, v in payload.items()
        if k not in ("signature", "_payload") and not str(k).startswith("_")
    }
    return hmac.new(
        _DEV_SECRET.encode(),
        canonical_json(body).encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(payload: dict[str, Any]) -> bool:
    sig = payload.get("signature") or ""
    if not sig or payload.get("realm") == "prod":
        return False
    expected = sign_payload(payload)
    return hmac.compare_digest(sig, expected)


def write_dev_key_stub(keys_dir: Path) -> Path:
    keys_dir.mkdir(parents=True, exist_ok=True)
    path = keys_dir / "stage2_dev_hmac.txt"
    path.write_text(
        f"realm={DEV_REALM}\nnote=DEV HMAC stub — not a production key\n",
        encoding="utf-8",
    )
    return path
