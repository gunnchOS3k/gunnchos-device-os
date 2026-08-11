"""Development-only Ed25519 signing keys for WP-013 release engineering.

CLAIM BOUNDARY: these keys are generated locally on demand, never committed
(``security/secure_boot/dev_keys/`` is gitignored), and are used only to sign
DEV/EVT/FACTORY/RECOVERY realm build metadata, A/B update manifests, and
gunnchSDK packages for lab/CI purposes. They are NOT production keys, are
NOT HSM-backed, and MUST NOT be treated as a production trust root.
PRODUCTION_SHIPPING_IMAGE_DEFINITION never uses these keys; production
builds remain unsigned and NOT_RELEASED.
"""
from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

CLAIM_BOUNDARY = (
    "Development-only Ed25519 signing keypair for WP-013 release engineering "
    "(image realm metadata, A/B update manifests, gunnchSDK packages). "
    "Not production keys, not HSM-backed, not a production trust root."
)

_KEY_DIR_REL = Path("security") / "secure_boot" / "dev_keys"
_PRIV_NAME = "release_engineering_ed25519_dev.pem"
_PUB_NAME = "release_engineering_ed25519_dev.pub.pem"


def dev_key_dir(repo_root: Path) -> Path:
    d = repo_root / _KEY_DIR_REL
    d.mkdir(parents=True, exist_ok=True)
    return d


def key_paths(repo_root: Path) -> tuple[Path, Path]:
    d = dev_key_dir(repo_root)
    return d / _PRIV_NAME, d / _PUB_NAME


def ensure_dev_keypair(repo_root: Path) -> tuple[Path, Path]:
    """Generate the DEV Ed25519 keypair on first use. Idempotent."""
    priv_path, pub_path = key_paths(repo_root)
    if not priv_path.exists():
        key = Ed25519PrivateKey.generate()
        priv_path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        priv_path.chmod(0o600)
        pub_path.write_bytes(
            key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return priv_path, pub_path


def load_private_key(repo_root: Path) -> Ed25519PrivateKey:
    priv_path, _ = ensure_dev_keypair(repo_root)
    return serialization.load_pem_private_key(priv_path.read_bytes(), password=None)


def load_public_key(repo_root: Path) -> Ed25519PublicKey:
    _, pub_path = ensure_dev_keypair(repo_root)
    return serialization.load_pem_public_key(pub_path.read_bytes())


def sign_bytes(repo_root: Path, payload: bytes) -> str:
    return load_private_key(repo_root).sign(payload).hex()


def verify_bytes(repo_root: Path, payload: bytes, signature_hex: str) -> bool:
    try:
        load_public_key(repo_root).verify(bytes.fromhex(signature_hex), payload)
        return True
    except Exception:
        return False


def dev_public_key_fingerprint(repo_root: Path) -> str:
    import hashlib

    _, pub_path = ensure_dev_keypair(repo_root)
    return hashlib.sha256(pub_path.read_bytes()).hexdigest()[:16]
