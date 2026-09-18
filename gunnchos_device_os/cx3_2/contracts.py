"""CX3.2 versioned contracts — CareerProfile + PortfolioSharePackage v1.

No accreditation / OB3 / CLR conformance claims.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

SCHEMA_NS = "gunnchos.cx3_2.contracts"

CONTRACT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "CareerProfile": {
        "schema": f"{SCHEMA_NS}.CareerProfile.v1",
        "required": [
            "profile_id", "owner_id", "display_name", "headline", "summary",
            "skills", "credential_refs", "portfolio_collection_refs", "artifact_refs",
            "projects", "education", "experience", "visibility", "provenance",
            "created_at", "updated_at", "certification_claimed",
        ],
        "properties": {
            "profile_id": {"type": "string"},
            "owner_id": {"type": "string"},
            "display_name": {"type": "string"},
            "headline": {"type": "string"},
            "summary": {"type": "string"},
            "skills": {"type": "array"},
            "credential_refs": {"type": "array"},
            "portfolio_collection_refs": {"type": "array"},
            "artifact_refs": {"type": "array"},
            "projects": {"type": "array"},
            "education": {"type": "array"},
            "experience": {"type": "array"},
            "contact": {"type": "object"},
            "links": {"type": "object"},
            "visibility": {"type": "object"},
            "provenance": {"type": "object"},
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "certification_claimed": {"const": False},
        },
    },
    "PortfolioSharePackage": {
        "schema": f"{SCHEMA_NS}.PortfolioSharePackage.v1",
        "required": [
            "package_id", "format", "created_at", "selected", "career_public",
            "credentials", "artifacts", "verification", "privacy_manifest",
            "hashes", "status_snapshot_at", "certification_claimed",
        ],
        "properties": {
            "package_id": {"type": "string"},
            "format": {"const": "gunnchos.portfolio_share_package.v1"},
            "created_at": {"type": "string"},
            "selected": {"type": "object"},
            "career_public": {"type": "object"},
            "credentials": {"type": "array"},
            "artifacts": {"type": "array"},
            "collections": {"type": "array"},
            "verification": {"type": "object"},
            "privacy_manifest": {"type": "object"},
            "hashes": {"type": "object"},
            "issuer_public_metadata": {"type": "array"},
            "status_snapshot_at": {"type": "string"},
            "certification_claimed": {"const": False},
        },
    },
}


def all_contract_names() -> List[str]:
    return sorted(CONTRACT_SCHEMAS.keys())


def dump_schemas() -> Dict[str, Dict[str, Any]]:
    return {k: dict(v) for k, v in CONTRACT_SCHEMAS.items()}


def validate_record(name: str, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    schema = CONTRACT_SCHEMAS.get(name)
    if not schema:
        return False, [f"unknown_contract:{name}"]
    errs: List[str] = []
    for req in schema["required"]:
        if req not in record:
            errs.append(f"missing:{req}")
    if record.get("certification_claimed") is not False:
        errs.append("certification_claimed_must_be_false")
    props = schema.get("properties") or {}
    claim = props.get("certification_claimed") or {}
    if claim.get("const") is False and record.get("certification_claimed") is not False:
        errs.append("certification_claimed_const_violated")
    fmt = props.get("format")
    if isinstance(fmt, dict) and "const" in fmt and record.get("format") != fmt["const"]:
        errs.append("format_mismatch")
    return (len(errs) == 0), errs
