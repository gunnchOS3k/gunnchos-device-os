"""Software keystore and encrypted-at-rest blob store.

Uses Fernet (cryptography) with a device-local key derived from a persisted
seed file. Honest boundary: software keystore only — not TPM/Secure Enclave.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

CLAIM_BOUNDARY = (
    "Software keystore with Fernet-at-rest. Not TPM, Secure Enclave, "
    "hardware-backed keys, or FIPS-validated module."
)


def _derive_fernet_key(seed: bytes) -> bytes:
    digest = hashlib.sha256(seed).digest()
    return base64.urlsafe_b64encode(digest)


@dataclass
class SoftwareKeystore:
    root: Path
    seed_path: Path = field(init=False)
    store_path: Path = field(init=False)
    _fernet: Fernet = field(init=False, repr=False)
    blobs: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.seed_path = self.root / "keystore.seed"
        self.store_path = self.root / "encrypted_blobs.json"
        seed = self._load_or_create_seed()
        self._fernet = Fernet(_derive_fernet_key(seed))
        if self.store_path.exists():
            self.blobs = json.loads(self.store_path.read_text(encoding="utf-8"))

    def _load_or_create_seed(self) -> bytes:
        if self.seed_path.exists():
            return self.seed_path.read_bytes()
        seed = os.urandom(32)
        self.seed_path.write_bytes(seed)
        return seed

    def put(self, key: str, plaintext: bytes, *, namespace: str = "default") -> dict[str, Any]:
        token = self._fernet.encrypt(plaintext).decode("ascii")
        rec = {
            "key": key,
            "namespace": namespace,
            "ciphertext": token,
            "stored_at_ms": int(time.time() * 1000),
            "software_keystore": True,
        }
        self.blobs[f"{namespace}:{key}"] = rec
        self._persist()
        return {"ok": True, "key": key, "namespace": namespace, "bytes": len(plaintext)}

    def get(self, key: str, *, namespace: str = "default") -> dict[str, Any]:
        rec = self.blobs.get(f"{namespace}:{key}")
        if rec is None:
            return {"ok": False, "error": "not_found"}
        try:
            plain = self._fernet.decrypt(rec["ciphertext"].encode("ascii"))
        except InvalidToken:
            return {"ok": False, "error": "decrypt_failed_tampered"}
        return {"ok": True, "plaintext": plain, "rec": rec}

    def delete(self, key: str, *, namespace: str = "default") -> dict[str, Any]:
        full = f"{namespace}:{key}"
        if full not in self.blobs:
            return {"ok": False, "error": "not_found"}
        del self.blobs[full]
        self._persist()
        return {"ok": True, "deleted": full}

    def _persist(self) -> None:
        self.store_path.write_text(json.dumps(self.blobs, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def status(self) -> dict[str, Any]:
        return {
            "schema": "gunnchos.platform.encrypted_storage.v1",
            "claim_boundary": CLAIM_BOUNDARY,
            "software_keystore": True,
            "tpm_backed": False,
            "blob_count": len(self.blobs),
            "seed_present": self.seed_path.exists(),
        }

    def export_metadata(self) -> dict[str, Any]:
        return {
            **self.status(),
            "keys": sorted(self.blobs.keys()),
        }
