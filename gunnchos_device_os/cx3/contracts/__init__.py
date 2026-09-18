"""Versioned CX3.1 contract schemas (v1).

Inspired by Open Badges 3 / CLR shapes — NOT conformance claims.
certification_claimed is always false.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

SCHEMA_NS = "gunnchos.cx3.contracts"

CONTRACT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "CredentialRecord": {
        "schema": f"{SCHEMA_NS}.CredentialRecord.v1",
        "required": [
            "credential_id",
            "type",
            "subject_profile_id",
            "issued_at",
            "issuer_id",
            "evidence_refs",
            "signature",
            "certification_claimed",
            "status",
        ],
        "properties": {
            "credential_id": {"type": "string"},
            "type": {"enum": ["OpenBadge3", "CLR2", "local_assertion"]},
            "subject_profile_id": {"type": "string"},
            "issued_at": {"type": "string"},
            "issuer_id": {"type": "string"},
            "evidence_refs": {"type": "array"},
            "signature": {"type": "object"},
            "certification_claimed": {"const": False},
            "status": {"enum": ["active", "revoked", "suspended"]},
            "name": {"type": "string"},
            "description": {"type": "string"},
        },
    },
    "EvidenceRecord": {
        "schema": f"{SCHEMA_NS}.EvidenceRecord.v1",
        "required": [
            "evidence_id",
            "source",
            "artifact_sha256",
            "artifact_path",
            "captured_at",
            "certification_claimed",
        ],
        "properties": {
            "evidence_id": {"type": "string"},
            "source": {"enum": ["vault", "learning", "lab", "import"]},
            "artifact_sha256": {"type": "string"},
            "artifact_path": {"type": "string"},
            "captured_at": {"type": "string"},
            "mime": {"type": "string"},
            "certification_claimed": {"const": False},
        },
    },
    "IssuerProfile": {
        "schema": f"{SCHEMA_NS}.IssuerProfile.v1",
        "required": [
            "issuer_id",
            "name",
            "algorithm",
            "public_key_b64",
            "ephemeral",
            "certification_claimed",
        ],
        "properties": {
            "issuer_id": {"type": "string"},
            "name": {"type": "string"},
            "algorithm": {"const": "Ed25519"},
            "public_key_b64": {"type": "string"},
            "ephemeral": {"type": "boolean"},
            "certification_claimed": {"const": False},
            "realm": {"enum": ["lab", "dev", "production_pending"]},
        },
    },
    "CredentialStatus": {
        "schema": f"{SCHEMA_NS}.CredentialStatus.v1",
        "required": ["credential_id", "status", "updated_at", "certification_claimed"],
        "properties": {
            "credential_id": {"type": "string"},
            "status": {"enum": ["active", "revoked", "suspended"]},
            "updated_at": {"type": "string"},
            "reason": {"type": "string"},
            "certification_claimed": {"const": False},
        },
    },
    "PortfolioArtifact": {
        "schema": f"{SCHEMA_NS}.PortfolioArtifact.v1",
        "required": [
            "artifact_id",
            "title",
            "visibility",
            "linked_credential_ids",
            "certification_claimed",
        ],
        "properties": {
            "artifact_id": {"type": "string"},
            "title": {"type": "string"},
            "visibility": {"enum": ["private", "selective", "public_local"]},
            "linked_credential_ids": {"type": "array"},
            "evidence_refs": {"type": "array"},
            "summary": {"type": "string"},
            "certification_claimed": {"const": False},
        },
    },
    "PortfolioCollection": {
        "schema": f"{SCHEMA_NS}.PortfolioCollection.v1",
        "required": [
            "collection_id",
            "owner_profile_id",
            "artifact_ids",
            "certification_claimed",
        ],
        "properties": {
            "collection_id": {"type": "string"},
            "owner_profile_id": {"type": "string"},
            "artifact_ids": {"type": "array"},
            "title": {"type": "string"},
            "certification_claimed": {"const": False},
        },
    },
    "CredentialExport": {
        "schema": f"{SCHEMA_NS}.CredentialExport.v1",
        "required": [
            "export_id",
            "format",
            "credentials",
            "exported_at",
            "certification_claimed",
        ],
        "properties": {
            "export_id": {"type": "string"},
            "format": {"enum": ["gunnchos.credential_export.v1", "ob3_inspired", "clr_inspired"]},
            "credentials": {"type": "array"},
            "exported_at": {"type": "string"},
            "certification_claimed": {"const": False},
            "include_private_keys": {"const": False},
        },
    },
    "PortfolioExport": {
        "schema": f"{SCHEMA_NS}.PortfolioExport.v1",
        "required": [
            "export_id",
            "format",
            "selected_artifact_ids",
            "manifest",
            "exported_at",
            "certification_claimed",
        ],
        "properties": {
            "export_id": {"type": "string"},
            "format": {"enum": ["portable_html_manifest.v1"]},
            "selected_artifact_ids": {"type": "array"},
            "manifest": {"type": "object"},
            "exported_at": {"type": "string"},
            "certification_claimed": {"const": False},
            "privacy_mode": {"enum": ["selective", "all_private_excluded"]},
        },
    },
}


def validate_record(kind: str, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Lightweight structural validation — fail closed on missing required / bad claim."""
    schema = CONTRACT_SCHEMAS.get(kind)
    if not schema:
        return False, [f"unknown_contract:{kind}"]
    errors: List[str] = []
    if record.get("certification_claimed") is not False:
        errors.append("certification_claimed_must_be_false")
    for key in schema["required"]:
        if key not in record:
            errors.append(f"missing:{key}")
    props = schema.get("properties") or {}
    for key, spec in props.items():
        if key not in record:
            continue
        if "const" in spec and record[key] != spec["const"]:
            errors.append(f"const_mismatch:{key}")
        if "enum" in spec and record[key] not in spec["enum"]:
            errors.append(f"enum_mismatch:{key}")
    return (len(errors) == 0), errors


def all_contract_names() -> List[str]:
    return sorted(CONTRACT_SCHEMAS.keys())


def dump_schemas() -> Dict[str, Any]:
    return copy.deepcopy(CONTRACT_SCHEMAS)
