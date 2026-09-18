"""Ephemeral lab Ed25519 issuer — private keys never committed."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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

from gunnchos_device_os.cx3.contracts import validate_record
from gunnchos_device_os.cx3.paths import issuer_ephemeral_root


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def canonical_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


@dataclass
class LabIssuer:
    issuer_id: str
    name: str
    private_key: Ed25519PrivateKey
    public_key_b64: str
    ephemeral: bool = True
    realm: str = "lab"

    def profile(self) -> Dict[str, Any]:
        return {
            "issuer_id": self.issuer_id,
            "name": self.name,
            "algorithm": "Ed25519",
            "public_key_b64": self.public_key_b64,
            "ephemeral": self.ephemeral,
            "certification_claimed": False,
            "realm": self.realm,
        }

    def sign_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        msg = canonical_bytes(payload)
        sig = self.private_key.sign(msg)
        return {
            "algorithm": "Ed25519",
            "public_key_b64": self.public_key_b64,
            "signature_b64": _b64(sig),
            "payload_sha256": hashlib.sha256(msg).hexdigest(),
        }


def create_ephemeral_issuer(
    *,
    name: str = "CX3 Lab Issuer",
    store_dir: Optional[Path] = None,
) -> LabIssuer:
    """Generate a fresh Ed25519 keypair under /tmp (never under repo)."""
    root = store_dir or issuer_ephemeral_root()
    root.mkdir(parents=True, exist_ok=True)
    # Refuse to write private keys into the git worktree.
    resolved = root.resolve()
    if "gunnchos-device-os" in str(resolved) and "/tmp" not in str(resolved):
        raise RuntimeError("REFUSE_COMMIT_PRIVATE_KEY_PATH")

    private_key = Ed25519PrivateKey.generate()
    pub = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    issuer_id = f"issuer:lab:{uuid.uuid4().hex[:12]}"
    issuer = LabIssuer(
        issuer_id=issuer_id,
        name=name,
        private_key=private_key,
        public_key_b64=_b64(pub),
        ephemeral=True,
        realm="lab",
    )
    # Persist private key only under /tmp with restrictive perms
    key_path = root / f"{issuer_id.replace(':', '_')}.pem"
    pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    fd = os.open(str(key_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, pem)
    finally:
        os.close(fd)
    (root / f"{issuer_id.replace(':', '_')}.pub.json").write_text(
        json.dumps(issuer.profile(), indent=2) + "\n"
    )
    # Ensure we never leave a copy named like a commit candidate in cwd
    return issuer


def load_public_key(public_key_b64: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(_b64d(public_key_b64))


def verify_signature(payload: Dict[str, Any], signature: Dict[str, Any]) -> Tuple[bool, str]:
    """Offline-capable Ed25519 verify. Fail closed."""
    if not signature or signature.get("algorithm") != "Ed25519":
        return False, "missing_or_bad_algorithm"
    try:
        pub = load_public_key(signature["public_key_b64"])
        msg = canonical_bytes(payload)
        expected = signature.get("payload_sha256")
        if expected and hashlib.sha256(msg).hexdigest() != expected:
            return False, "payload_digest_mismatch"
        pub.verify(_b64d(signature["signature_b64"]), msg)
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 — fail closed
        return False, f"verify_failed:{type(exc).__name__}"


def issue_evidence_bound_credential(
    issuer: LabIssuer,
    *,
    subject_profile_id: str,
    evidence: Dict[str, Any],
    name: str = "Learning evidence assertion",
    description: str = "Local lab assertion bound to Vault artifact. Not a certification.",
    cred_type: str = "local_assertion",
) -> Dict[str, Any]:
    """Issue a signed CredentialRecord bound to real evidence (Vault hash)."""
    ok_e, errs_e = validate_record("EvidenceRecord", evidence)
    if not ok_e:
        raise ValueError(f"invalid_evidence:{errs_e}")
    if not evidence.get("artifact_sha256") or len(evidence["artifact_sha256"]) != 64:
        raise ValueError("evidence_sha256_required")

    credential_id = f"cred:{uuid.uuid4().hex}"
    issued_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    unsigned = {
        "credential_id": credential_id,
        "type": cred_type,
        "subject_profile_id": subject_profile_id,
        "issued_at": issued_at,
        "issuer_id": issuer.issuer_id,
        "evidence_refs": [evidence["evidence_id"]],
        "evidence": {
            "evidence_id": evidence["evidence_id"],
            "artifact_sha256": evidence["artifact_sha256"],
            "artifact_path": evidence.get("artifact_path"),
            "source": evidence.get("source"),
        },
        "name": name,
        "description": description,
        "certification_claimed": False,
        "status": "active",
        "nonce": secrets.token_hex(8),
    }
    # Sign without the signature field itself
    sig = issuer.sign_payload(unsigned)
    record = {**unsigned, "signature": sig}
    ok, errs = validate_record("CredentialRecord", record)
    if not ok:
        raise ValueError(f"invalid_credential:{errs}")
    return record


def unsigned_payload_from_credential(cred: Dict[str, Any]) -> Dict[str, Any]:
    body = dict(cred)
    body.pop("signature", None)
    return body


def verify_credential(
    cred: Dict[str, Any],
    *,
    expected_evidence_sha256: Optional[str] = None,
    status_lookup: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Verify signature, evidence bind, and optional status. Fail closed."""
    result: Dict[str, Any] = {
        "verified": False,
        "tampered": False,
        "revoked": False,
        "offline_capable": True,
        "certification_claimed": False,
        "reasons": [],
    }
    if cred.get("certification_claimed") is not False:
        result["reasons"].append("certification_claimed_not_false")
        return result
    ok, errs = validate_record("CredentialRecord", cred)
    if not ok:
        result["reasons"].extend(errs)
        return result
    payload = unsigned_payload_from_credential(cred)
    sig_ok, reason = verify_signature(payload, cred.get("signature") or {})
    if not sig_ok:
        result["tampered"] = True
        result["reasons"].append(reason)
        return result
    bound = (cred.get("evidence") or {}).get("artifact_sha256")
    if expected_evidence_sha256 and bound != expected_evidence_sha256:
        result["tampered"] = True
        result["reasons"].append("evidence_bind_mismatch")
        return result
    status = cred.get("status") or "active"
    if status_lookup is not None:
        status = status_lookup.get(cred["credential_id"], status)
    if status == "revoked":
        result["revoked"] = True
        result["reasons"].append("revoked")
        return result
    if status != "active":
        result["reasons"].append(f"status:{status}")
        return result
    result["verified"] = True
    result["reasons"].append("ok")
    return result


def detect_tamper(cred: Dict[str, Any]) -> Dict[str, Any]:
    """Flip a claim field and confirm verification fails."""
    original = verify_credential(cred)
    mutated = json.loads(json.dumps(cred))
    mutated["name"] = (mutated.get("name") or "") + " TAMPERED"
    after = verify_credential(mutated)
    return {
        "original_verified": bool(original.get("verified")),
        "mutated_verified": bool(after.get("verified")),
        "tamper_detected": bool(original.get("verified")) and not bool(after.get("verified")),
        "mutated_reasons": after.get("reasons"),
    }
