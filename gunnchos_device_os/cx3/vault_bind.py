"""Bind CX3 credentials to real Vault journey artifacts from prior waves."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


KNOWN_VAULT_SHA256 = "e72f5b8c2940c253d8dc7d7797318de2a0fa2b394f0d4caca1e6495b87e13fd6"
KNOWN_VAULT_PATH = "cx2h2_j1_essay.odt"


def load_vault_evidence(repo: Path) -> Dict[str, Any]:
    """Prefer live CX2H2 vault proof; fall back to known sha only if proof file exists."""
    proof_path = (
        repo
        / "artifacts"
        / "complete_experience"
        / "cx2h2"
        / "CX2H2_VAULT_FILE_PROVIDER_PROOF.json"
    )
    out: Dict[str, Any] = {
        "ok": False,
        "certification_claimed": False,
        "source_path": str(proof_path),
    }
    if not proof_path.is_file():
        out["blocker"] = "CX2H2_VAULT_PROOF_MISSING"
        return out
    proof = json.loads(proof_path.read_text())
    file_meta = proof.get("file") or {}
    sha = file_meta.get("sha256")
    path = file_meta.get("path")
    if not sha or not path:
        out["blocker"] = "CX2H2_VAULT_PROOF_INCOMPLETE"
        return out
    if not proof.get("CX2H2_REAL_VAULT_FILE_PASS"):
        out["blocker"] = "CX2H2_REAL_VAULT_FILE_PASS_FALSE"
        return out
    evidence = {
        "evidence_id": f"ev:vault:{uuid.uuid4().hex[:12]}",
        "source": "vault",
        "artifact_sha256": sha,
        "artifact_path": path,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mime": file_meta.get("mime") or "application/octet-stream",
        "certification_claimed": False,
        "provenance": {
            "wave": "CX2H.2",
            "proof": "CX2H2_VAULT_FILE_PROVIDER_PROOF.json",
            "CX2H2_REAL_VAULT_FILE_PASS": True,
        },
    }
    out.update(
        {
            "ok": True,
            "evidence": evidence,
            "matches_known_j1_essay": sha == KNOWN_VAULT_SHA256 and path == KNOWN_VAULT_PATH,
        }
    )
    return out


def load_cx2h4_gate(repo: Path) -> Dict[str, Any]:
    tokens_path = (
        repo / "artifacts" / "complete_experience" / "cx2h4" / "CX2H4_TOKENS.json"
    )
    if not tokens_path.is_file():
        return {"ok": False, "CX2H4_P0_DIGITAL_CLOSURE_PASS": False, "blocker": "CX2H4_TOKENS_MISSING"}
    tokens = json.loads(tokens_path.read_text())
    return {
        "ok": bool(tokens.get("CX2H4_P0_DIGITAL_CLOSURE_PASS")),
        "CX2H4_P0_DIGITAL_CLOSURE_PASS": bool(tokens.get("CX2H4_P0_DIGITAL_CLOSURE_PASS")),
        "J1_CLASS": tokens.get("J1_CLASS"),
        "J2_CLASS": tokens.get("J2_CLASS"),
        "J3_CLASS": tokens.get("J3_CLASS"),
        "J4_CLASS": tokens.get("J4_CLASS"),
        "J5_CLASS": tokens.get("J5_CLASS"),
        "J6_CLASS": tokens.get("J6_CLASS") or "HUMAN_VALIDATION_PENDING",
        "J7_CLASS": tokens.get("J7_CLASS"),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": bool(tokens.get("FULL_COMPLETE_EXPERIENCE_COMPLETE")),
        "source": str(tokens_path),
    }
