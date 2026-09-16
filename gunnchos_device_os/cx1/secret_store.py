"""Encrypted-secret storage abstraction — never stores plaintext passwords."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


def _xor_obfuscate(data: bytes, key: bytes) -> bytes:
    """Local test-safe obfuscation when OS keyring is unavailable.

    Not a substitute for hardware-backed keyring; claim_boundary reflects that.
    """
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


@dataclass
class SecretStore:
    """Profile-scoped secret store with keyring preferred, file fallback."""

    root: Path
    backend: str = "file_obfuscated"
    _key: bytes = field(default_factory=lambda: secrets.token_bytes(32), repr=False)
    _memory: Dict[str, bytes] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        key_path = self.root / ".store_key"
        if key_path.exists():
            self._key = key_path.read_bytes()
        else:
            key_path.write_bytes(self._key)
            try:
                os.chmod(key_path, 0o600)
            except OSError:
                pass
        try:
            import keyring  # type: ignore

            keyring.get_keyring()
            self.backend = "keyring"
        except Exception:
            self.backend = "file_obfuscated"

    def put(self, namespace: str, name: str, secret: str) -> None:
        if not secret:
            raise ValueError("empty_secret_rejected")
        payload = secret.encode("utf-8")
        if self.backend == "keyring":
            try:
                import keyring  # type: ignore

                keyring.set_password(f"gunnchos.cx1.{namespace}", name, secret)
                return
            except Exception:
                self.backend = "file_obfuscated"
        blob = _xor_obfuscate(payload, self._key)
        path = self.root / f"{namespace}__{name}.sec"
        path.write_bytes(blob)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        self._memory[f"{namespace}:{name}"] = blob

    def get(self, namespace: str, name: str) -> Optional[str]:
        if self.backend == "keyring":
            try:
                import keyring  # type: ignore

                value = keyring.get_password(f"gunnchos.cx1.{namespace}", name)
                if value is not None:
                    return value
            except Exception:
                self.backend = "file_obfuscated"
        path = self.root / f"{namespace}__{name}.sec"
        if not path.exists():
            return None
        return _xor_obfuscate(path.read_bytes(), self._key).decode("utf-8")

    def delete(self, namespace: str, name: str) -> bool:
        if self.backend == "keyring":
            try:
                import keyring  # type: ignore

                keyring.delete_password(f"gunnchos.cx1.{namespace}", name)
            except Exception:
                pass
        path = self.root / f"{namespace}__{name}.sec"
        if path.exists():
            path.unlink()
            return True
        return False

    def password_hash(self, password: str, salt: bytes | None = None) -> dict:
        """Store only salted hash — never plaintext passwords."""
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return {
            "algo": "pbkdf2_sha256",
            "iterations": 120_000,
            "salt_hex": salt.hex(),
            "hash_hex": digest.hex(),
        }

    def verify_password(self, password: str, record: dict) -> bool:
        salt = bytes.fromhex(record["salt_hex"])
        check = self.password_hash(password, salt=salt)
        return secrets.compare_digest(check["hash_hex"], record["hash_hex"])

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "root": str(self.root),
            "claim_boundary": "keyring_preferred_file_obfuscation_fallback_not_hsm",
        }
