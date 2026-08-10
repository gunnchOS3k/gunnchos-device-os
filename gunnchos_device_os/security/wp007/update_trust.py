"""Asymmetric update verification for DEV/TEST (WP007-IV-RES-001).

Uses cryptography Ed25519. DEV_TEST_TRUST_ROOT is pinned; PRODUCTION_TRUST_ROOT
remains EXTERNAL_PENDING. No production private key is committed.
"""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

DEV_TEST_TRUST_ROOT = "DEV_TEST_TRUST_ROOT"
PRODUCTION_TRUST_ROOT = "PRODUCTION_TRUST_ROOT"
PRODUCTION_TRUST_STATUS = "EXTERNAL_PENDING"

# Deterministic DEV-only seed → keypair for local signing helpers / tests.
# Public key is the pinned trust root; private material must never be labeled prod.
_DEV_SEED = hashlib.sha256(b"gunnchos-wp007-dev-test-trust-root-v1:NOT-PRODUCTION").digest()


def _dev_private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(_DEV_SEED)


def _dev_public_key() -> Ed25519PublicKey:
    return _dev_private_key().public_key()


def pinned_dev_public_key_b64() -> str:
    raw = _dev_public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return base64.b64encode(raw).decode("ascii")


def trust_metadata() -> dict[str, Any]:
    return {
        "schema": "gunnchos.wp007.update_trust.v1",
        "DEV_TEST_TRUST_ROOT": {
            "algorithm": "Ed25519",
            "public_key_b64": pinned_dev_public_key_b64(),
            "realm": DEV_TEST_TRUST_ROOT,
            "library": "cryptography",
            "note": "Pinned DEV/TEST trust root only",
        },
        "PRODUCTION_TRUST_ROOT": PRODUCTION_TRUST_STATUS,
        "production_private_key_committed": False,
        "claim_boundary": (
            "DEV/TEST asymmetric verification only. "
            f"{PRODUCTION_TRUST_ROOT}={PRODUCTION_TRUST_STATUS}."
        ),
    }


def canonical_signed_bytes(
    *,
    version: str,
    security_version: int,
    digest_sha256: str,
    metadata: dict[str, Any] | None,
) -> bytes:
    body = {
        "digest_sha256": digest_sha256,
        "metadata": metadata or {},
        "security_version": int(security_version),
        "version": str(version),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def sign_update_package(
    *,
    version: str,
    security_version: int,
    digest_sha256: str,
    metadata: dict[str, Any] | None = None,
    private_key: Ed25519PrivateKey | None = None,
) -> dict[str, Any]:
    """Sign intended payload/metadata under DEV_TEST_TRUST_ROOT.

    Callers may inject an alternate private key for negative tests only.
    """
    key = private_key or _dev_private_key()
    msg = canonical_signed_bytes(
        version=version,
        security_version=security_version,
        digest_sha256=digest_sha256,
        metadata=metadata,
    )
    sig = key.sign(msg)
    return {
        "version": version,
        "security_version": int(security_version),
        "digest_sha256": digest_sha256,
        "metadata": dict(metadata or {}),
        "signature_b64": base64.b64encode(sig).decode("ascii"),
        "trust_realm": DEV_TEST_TRUST_ROOT,
        "algorithm": "Ed25519",
        "production_keys_used": False,
    }


@dataclass(frozen=True)
class VerifyResult:
    verified: bool
    reason: str
    trust_realm: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "verified": self.verified,
            "reason": self.reason,
            "trust_realm": self.trust_realm,
            "PRODUCTION_TRUST_ROOT": PRODUCTION_TRUST_STATUS,
            "production_keys_used": False,
        }
        if self.details:
            out["details"] = self.details
        return out


def verify_update_package(
    package: dict[str, Any] | None,
    *,
    active_security_version: int = 1,
    force_verified: bool | None = None,
    pinned_public_key_b64: str | None = None,
) -> VerifyResult:
    """Verify real Ed25519 signature bytes against pinned DEV trust root.

    ``force_verified`` is accepted only to prove callers cannot override:
    it is ignored and cannot make verified=True.
    """
    _ = force_verified  # deliberately ignored — caller cannot force success

    if not package:
        return VerifyResult(False, "no_package")

    realm = str(package.get("trust_realm") or "")
    if realm == PRODUCTION_TRUST_ROOT or package.get("production_keys_used") is True:
        return VerifyResult(
            False,
            "production_trust_external_pending",
            trust_realm=PRODUCTION_TRUST_ROOT,
            details={"PRODUCTION_TRUST_ROOT": PRODUCTION_TRUST_STATUS},
        )
    if realm and realm != DEV_TEST_TRUST_ROOT:
        return VerifyResult(False, "untrusted_realm", trust_realm=realm)

    sig_b64 = package.get("signature_b64")
    if sig_b64 is None or sig_b64 == "":
        return VerifyResult(False, "missing_signature")
    if not isinstance(sig_b64, str):
        return VerifyResult(False, "malformed_signature")

    try:
        sig = base64.b64decode(sig_b64, validate=True)
    except Exception:
        return VerifyResult(False, "malformed_signature")
    if len(sig) != 64:
        return VerifyResult(False, "malformed_signature")

    try:
        security_version = int(package.get("security_version"))
    except (TypeError, ValueError):
        return VerifyResult(False, "bad_security_version")

    if security_version < int(active_security_version):
        return VerifyResult(
            False,
            "anti_rollback_security_version",
            trust_realm=DEV_TEST_TRUST_ROOT,
            details={
                "package_sv": security_version,
                "active_sv": int(active_security_version),
            },
        )

    version = package.get("version")
    digest = package.get("digest_sha256")
    if not isinstance(version, str) or not version:
        return VerifyResult(False, "bad_version")
    if not isinstance(digest, str) or len(digest) != 64:
        return VerifyResult(False, "bad_digest")

    metadata = package.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        return VerifyResult(False, "bad_metadata")

    msg = canonical_signed_bytes(
        version=version,
        security_version=security_version,
        digest_sha256=digest,
        metadata=metadata,
    )

    pub_b64 = pinned_public_key_b64 or pinned_dev_public_key_b64()
    try:
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64, validate=True))
    except Exception:
        return VerifyResult(False, "untrusted_public_key")

    try:
        pub.verify(sig, msg)
    except Exception:
        return VerifyResult(False, "signature_invalid", trust_realm=DEV_TEST_TRUST_ROOT)

    return VerifyResult(True, "ok", trust_realm=DEV_TEST_TRUST_ROOT)


def export_dev_public_pem() -> bytes:
    return _dev_public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)


def export_dev_private_pem_for_tests_only() -> bytes:
    """DEV-only private PEM for negative/unit tests — never treat as production."""
    return _dev_private_key().private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    )


def alternate_untrusted_private_key() -> Ed25519PrivateKey:
    seed = hashlib.sha256(b"gunnchos-wp007-WRONG-KEY-for-negative-tests").digest()
    return Ed25519PrivateKey.from_private_bytes(seed)
