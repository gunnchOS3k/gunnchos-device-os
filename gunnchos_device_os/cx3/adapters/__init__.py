"""OB3 / CLR inspired adapters — shape mapping only, no conformance claims."""

from __future__ import annotations

from typing import Any, Dict


ADAPTER_DISCLAIMER = (
    "OB3/CLR-inspired local adapter only. "
    "No Open Badges 3 or CLR conformance is claimed. "
    "certification_claimed=false always."
)


def to_ob3_inspired(credential: Dict[str, Any]) -> Dict[str, Any]:
    if credential.get("certification_claimed") is not False:
        raise ValueError("certification_claimed_must_be_false")
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "id": credential.get("credential_id"),
        "issuer": {"id": credential.get("issuer_id")},
        "validFrom": credential.get("issued_at"),
        "credentialSubject": {
            "id": credential.get("subject_profile_id"),
            "achievement": {
                "name": credential.get("name"),
                "description": credential.get("description"),
                "certification_claimed": False,
            },
        },
        "evidence": credential.get("evidence"),
        "proof": {
            "type": "DataIntegrityProof",
            "cryptosuite": "eddsa-rdfc-2022-inspired-local",
            "proofValue": (credential.get("signature") or {}).get("signature_b64"),
            "verificationMethod": (credential.get("signature") or {}).get("public_key_b64"),
        },
        "gunnchos": {
            "adapter": "ob3_inspired_v1",
            "conformance_claimed": False,
            "certification_claimed": False,
            "disclaimer": ADAPTER_DISCLAIMER,
            "native": credential,
        },
    }


def to_clr_inspired(credential: Dict[str, Any]) -> Dict[str, Any]:
    if credential.get("certification_claimed") is not False:
        raise ValueError("certification_claimed_must_be_false")
    return {
        "type": "ClrCredential",
        "id": credential.get("credential_id"),
        "issuer": credential.get("issuer_id"),
        "issuedOn": credential.get("issued_at"),
        "learner": {"id": credential.get("subject_profile_id")},
        "assertions": [
            {
                "id": credential.get("credential_id"),
                "achievement": {
                    "name": credential.get("name"),
                    "description": credential.get("description"),
                },
                "evidence": [credential.get("evidence")],
                "certification_claimed": False,
            }
        ],
        "gunnchos": {
            "adapter": "clr_inspired_v1",
            "conformance_claimed": False,
            "certification_claimed": False,
            "disclaimer": ADAPTER_DISCLAIMER,
            "native": credential,
        },
    }


def roundtrip_ok(credential: Dict[str, Any]) -> Dict[str, Any]:
    ob3 = to_ob3_inspired(credential)
    clr = to_clr_inspired(credential)
    native_ob3 = (ob3.get("gunnchos") or {}).get("native") or {}
    native_clr = (clr.get("gunnchos") or {}).get("native") or {}
    return {
        "ok": (
            native_ob3.get("credential_id") == credential.get("credential_id")
            and native_clr.get("credential_id") == credential.get("credential_id")
            and ob3.get("gunnchos", {}).get("conformance_claimed") is False
            and clr.get("gunnchos", {}).get("conformance_claimed") is False
            and ob3.get("gunnchos", {}).get("certification_claimed") is False
            and clr.get("gunnchos", {}).get("certification_claimed") is False
        ),
        "ob3_inspired": ob3,
        "clr_inspired": clr,
        "certification_claimed": False,
        "conformance_claimed": False,
    }
