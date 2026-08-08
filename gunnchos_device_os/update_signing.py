"""DEV-only update package signing — not production release signing.

Pairs with attestation DEV realm. Rejects PROD realm signing requests.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from gunnchos_device_os.identity import sha256_text, utc_now_iso


CLAIM_BOUNDARY = (
    "DEV-only update signing. No production code-signing certificate, "
    "no hardware security module, no store/OEM trust chain."
)

DEV_REALM_LABEL = "gunnchos-dev-update-signing-realm-v1"
DEV_REALM_SECRET = sha256_text(f"{DEV_REALM_LABEL}:not-a-production-key")[:64]


class SigningRealm(str, Enum):
    DEV = "dev"
    PROD = "prod"


@dataclass
class UpdatePackageManifest:
    package_id: str
    version: str
    artifact_sha256: str
    channel: str = "evt-alpha"
    security_version: int = 1
    realm: SigningRealm = SigningRealm.DEV
    created_at: str = field(default_factory=utc_now_iso)
    signature: str = ""

    def unsigned_body(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "version": self.version,
            "artifact_sha256": self.artifact_sha256,
            "channel": self.channel,
            "security_version": self.security_version,
            "realm": self.realm.value,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        body = self.unsigned_body()
        body["signature"] = self.signature
        body["claim_boundary"] = CLAIM_BOUNDARY
        body["mock"] = False
        return body


def _sign(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(
        DEV_REALM_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def sign_update_dev(manifest: UpdatePackageManifest) -> UpdatePackageManifest:
    if manifest.realm != SigningRealm.DEV:
        raise ValueError("PROD realm signing is rejected — no production keys")
    if len(manifest.artifact_sha256) != 64:
        raise ValueError("artifact_sha256 must be 64 hex chars")
    manifest.signature = _sign(manifest.unsigned_body())
    return manifest


def verify_update_signature(doc: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    required = (
        "package_id", "version", "artifact_sha256", "channel",
        "security_version", "realm", "created_at", "signature",
    )
    for key in required:
        if key not in doc:
            errors.append(f"missing_field:{key}")
    if errors:
        return {"valid": False, "errors": errors, "mock": False, "claim_boundary": CLAIM_BOUNDARY}

    if doc["realm"] == SigningRealm.PROD.value:
        return {
            "valid": False,
            "errors": ["prod_realm_rejected_no_production_keys"],
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    if doc["realm"] != SigningRealm.DEV.value:
        return {
            "valid": False,
            "errors": ["invalid_realm"],
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    body = {k: doc[k] for k in (
        "package_id", "version", "artifact_sha256", "channel",
        "security_version", "realm", "created_at",
    )}
    expected = _sign(body)
    if not hmac.compare_digest(expected, doc.get("signature", "")):
        errors.append("bad_signature")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "package_id": doc["package_id"],
        "version": doc["version"],
        "realm": doc["realm"],
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def build_signed_update(
    package_id: str,
    version: str,
    artifact_bytes: bytes,
    *,
    channel: str = "evt-alpha",
    security_version: int = 1,
) -> dict[str, Any]:
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    manifest = UpdatePackageManifest(
        package_id=package_id,
        version=version,
        artifact_sha256=digest,
        channel=channel,
        security_version=security_version,
        realm=SigningRealm.DEV,
    )
    sign_update_dev(manifest)
    return manifest.to_dict()
