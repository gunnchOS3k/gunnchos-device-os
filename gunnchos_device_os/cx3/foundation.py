"""Host-side CX3.1 foundation proofs (Wallet + Portfolio authorities)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx3.adapters import roundtrip_ok
from gunnchos_device_os.cx3.audit import security_fail_closed_audit
from gunnchos_device_os.cx3.contracts import all_contract_names, dump_schemas, validate_record
from gunnchos_device_os.cx3.issuer import (
    create_ephemeral_issuer,
    detect_tamper,
    issue_evidence_bound_credential,
    verify_credential,
)
from gunnchos_device_os.cx3.learning_evidence import LearningEvidenceProvider
from gunnchos_device_os.cx3.paths import (
    ensure_lab_tree,
    portfolio_data_root,
    wallet_data_root,
)
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3.vault_bind import load_cx2h4_gate, load_vault_evidence
from gunnchos_device_os.cx3.wallet import CredentialWallet


def run_foundation(repo: Path) -> Dict[str, Any]:
    """Execute all host-side CX3.1 proofs. Returns facts + token hints."""
    lab = ensure_lab_tree(repo)
    facts: Dict[str, Any] = {"wave": "CX3.1", "certification_claimed": False}
    token_hints: Dict[str, Any] = {}

    gate = load_cx2h4_gate(repo)
    facts["CX3_CX2H4_GATE"] = gate
    token_hints["CX2H4_P0_DIGITAL_CLOSURE_PASS"] = bool(gate.get("CX2H4_P0_DIGITAL_CLOSURE_PASS"))
    for j in ("J1_CLASS", "J2_CLASS", "J3_CLASS", "J4_CLASS", "J5_CLASS", "J6_CLASS", "J7_CLASS"):
        if gate.get(j):
            token_hints[j] = gate[j]
    if gate.get("FULL_COMPLETE_EXPERIENCE_COMPLETE"):
        token_hints["lab_blocker"] = "PRIOR_GATE_CLAIMED_FULL_COMPLETE"
        facts["blocked"] = True
        return {"facts": facts, "token_hints": token_hints}

    # Contracts v1
    schemas = dump_schemas()
    names = all_contract_names()
    expected = {
        "CredentialRecord",
        "EvidenceRecord",
        "IssuerProfile",
        "CredentialStatus",
        "PortfolioArtifact",
        "PortfolioCollection",
        "CredentialExport",
        "PortfolioExport",
    }
    contracts_ok = set(names) == expected and all(
        schemas[n].get("properties", {}).get("certification_claimed", {}).get("const") is False
        for n in names
    )
    facts["CX3_CONTRACTS_V1"] = {"ok": contracts_ok, "contracts": sorted(names), "schemas": schemas}
    token_hints["CX3_CONTRACTS_V1_PASS"] = contracts_ok

    # Ephemeral issuer
    issuer = create_ephemeral_issuer(name="CX3 Lab Issuer")
    issuer_prof = issuer.profile()
    ok_i, errs_i = validate_record("IssuerProfile", issuer_prof)
    # Confirm private key not under repo
    priv_in_repo = any(
        p.suffix in {".pem", ".key"} and "cx3" in str(p)
        for p in (repo / "gunnchos_device_os" / "cx3").rglob("*")
        if p.is_file()
    )
    issuer_ok = ok_i and issuer_prof.get("ephemeral") is True and not priv_in_repo
    facts["CX3_LAB_ISSUER_ED25519"] = {
        "ok": issuer_ok,
        "issuer": issuer_prof,
        "validate_errors": errs_i,
        "private_key_in_repo": priv_in_repo,
    }
    token_hints["CX3_LAB_ISSUER_ED25519_PASS"] = issuer_ok

    # Vault-bound evidence issuance
    vault = load_vault_evidence(repo)
    facts["vault_bind"] = vault
    evidence_ok = False
    credential = None
    if vault.get("ok"):
        evidence = vault["evidence"]
        credential = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=evidence,
            name="Vault-bound learning evidence assertion",
            description=(
                "Signed local assertion bound to CX2H2 Vault artifact. "
                "Not a degree, diploma, accreditation, or certification."
            ),
        )
        evidence_ok = (
            credential.get("certification_claimed") is False
            and credential.get("evidence", {}).get("artifact_sha256") == evidence["artifact_sha256"]
        )
    facts["CX3_EVIDENCE_BOUND_ISSUANCE"] = {
        "ok": evidence_ok,
        "credential_id": (credential or {}).get("credential_id"),
        "evidence_sha256": (vault.get("evidence") or {}).get("artifact_sha256"),
    }
    token_hints["CX3_EVIDENCE_BOUND_ISSUANCE_PASS"] = evidence_ok

    # Wallet storage
    wallet_root = wallet_data_root(repo)
    if wallet_root.exists():
        shutil.rmtree(wallet_root)
    wallet = CredentialWallet(wallet_root)
    wallet_ok = False
    if credential:
        wallet.put(credential)
        loaded = wallet.get(credential["credential_id"])
        wallet_ok = loaded is not None and loaded.get("credential_id") == credential["credential_id"]
    facts["CX3_WALLET_STORAGE"] = {"ok": wallet_ok, "root": str(wallet_root)}
    token_hints["CX3_WALLET_STORAGE_PASS"] = wallet_ok

    # Tamper / revoke / offline / import-export
    tamper = detect_tamper(credential) if credential else {"tamper_detected": False}
    token_hints["CX3_TAMPER_DETECT_PASS"] = bool(tamper.get("tamper_detected"))
    facts["CX3_TAMPER_DETECT"] = tamper

    revoke_ok = False
    offline_ok = False
    if credential:
        offline = verify_credential(credential, status_lookup=wallet.status_map())
        offline_ok = bool(offline.get("verified")) and bool(offline.get("offline_capable", True))
        rev = wallet.revoke(credential["credential_id"], reason="cx3_lab_status_demo")
        after = wallet.verify(credential["credential_id"])
        revoke_ok = bool(rev.get("ok")) and after.get("revoked") is True and after.get("verified") is False
        # Re-issue fresh active credential for remaining flows
        credential = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Vault-bound learning evidence assertion",
        )
        wallet.put(credential)
    facts["CX3_REVOCATION_STATUS"] = {"ok": revoke_ok}
    facts["CX3_OFFLINE_VERIFY"] = {"ok": offline_ok}
    token_hints["CX3_REVOCATION_STATUS_PASS"] = revoke_ok
    token_hints["CX3_OFFLINE_VERIFY_PASS"] = offline_ok

    export_obj = wallet.export_credentials()
    # Round-trip into a fresh wallet dir
    import_root = lab / "work" / "wallet_import"
    if import_root.exists():
        shutil.rmtree(import_root)
    wallet2 = CredentialWallet(import_root)
    imp = wallet2.import_credentials(export_obj)
    # Negative: reject certification_claimed true
    bad = json.loads(json.dumps(export_obj))
    bad["certification_claimed"] = True
    bad_imp = wallet2.import_credentials(bad)
    iex_ok = bool(imp.get("ok")) and bad_imp.get("ok") is False
    facts["CX3_IMPORT_EXPORT"] = {
        "ok": iex_ok,
        "imported": imp.get("imported"),
        "rejected_bad_claim": bad_imp,
    }
    token_hints["CX3_IMPORT_EXPORT_PASS"] = iex_ok

    # OB3/CLR adapters
    adapter = roundtrip_ok(credential) if credential else {"ok": False}
    facts["CX3_OB3_CLR_ADAPTER"] = {
        "ok": bool(adapter.get("ok")),
        "conformance_claimed": False,
        "certification_claimed": False,
    }
    token_hints["CX3_OB3_CLR_ADAPTER_PASS"] = bool(adapter.get("ok"))

    # Portfolio
    portfolio_root = portfolio_data_root(repo)
    if portfolio_root.exists():
        shutil.rmtree(portfolio_root)
    portfolio = PortfolioStore(portfolio_root)
    art_public = portfolio.upsert_artifact(
        {
            "title": "J1 essay evidence summary",
            "visibility": "selective",
            "linked_credential_ids": [credential["credential_id"]] if credential else [],
            "summary": "Learning evidence linked to Vault essay — not a certification.",
            "evidence_refs": [vault["evidence"]["evidence_id"]] if vault.get("ok") else [],
        }
    )
    art_private = portfolio.upsert_artifact(
        {
            "title": "Private reflection notes",
            "visibility": "private",
            "linked_credential_ids": [],
            "summary": "Kept private unless explicitly selected.",
        }
    )
    portfolio.upsert_collection(
        {
            "title": "CX3 lab portfolio",
            "artifact_ids": [art_public["artifact_id"], art_private["artifact_id"]],
        }
    )
    # Selective export excludes unselected private
    exported = portfolio.selective_export(
        [art_public["artifact_id"]],
        title="CX3 Portable Portfolio",
        credentials=[credential] if credential else [],
    )
    manifest = exported["export"]["manifest"]
    privacy_ok = (
        art_private["artifact_id"] in (manifest.get("skipped_private_unselected") or [])
        and art_public["artifact_id"] in exported["export"]["selected_artifact_ids"]
        and exported["export"].get("certification_claimed") is False
    )
    package_dir = Path(exported["package_dir"])
    portable_ok = (
        (package_dir / "index.html").is_file()
        and (package_dir / "manifest.json").is_file()
        and "certification_claimed=false" in (package_dir / "index.html").read_text()
    )
    facts["CX3_PORTFOLIO_PRIVACY_EXPORT"] = {"ok": privacy_ok, "export_id": exported["export"]["export_id"]}
    facts["CX3_PORTFOLIO_PORTABLE_PACKAGE"] = {
        "ok": portable_ok,
        "package_dir": str(package_dir),
        "files": exported.get("files"),
    }
    token_hints["CX3_PORTFOLIO_PRIVACY_EXPORT_PASS"] = privacy_ok
    token_hints["CX3_PORTFOLIO_PORTABLE_PACKAGE_PASS"] = portable_ok

    # LearningEvidenceProvider seam
    lep = LearningEvidenceProvider(vault_evidence=vault.get("evidence"))
    seam = lep.seam_status()
    facts["WAIKE_INTEGRATION_SEAM"] = seam
    token_hints["WAIKE_INTEGRATION_SEAM_PASS"] = bool(seam.get("WAIKE_INTEGRATION_SEAM_PASS"))
    token_hints["WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = bool(
        seam.get("WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS")
    )

    # Security
    security = security_fail_closed_audit(repo)
    facts["CX3_SECURITY_FAIL_CLOSED"] = security
    token_hints["CX3_SECURITY_FAIL_CLOSED_PASS"] = bool(security.get("CX3_SECURITY_FAIL_CLOSED_PASS"))

    # Persist active credential id for GUI provider
    seed = {
        "credential_id": credential.get("credential_id") if credential else None,
        "issuer": issuer_prof,
        "wallet_root": str(wallet_root),
        "portfolio_root": str(portfolio_root),
        "certification_claimed": False,
    }
    (lab / "work" / "foundation_seed.json").write_text(json.dumps(seed, indent=2) + "\n")
    facts["foundation_seed"] = seed
    facts["foundation"] = {"ok": True, "certification_claimed": False}
    return {"facts": facts, "token_hints": token_hints, "credential": credential, "wallet": wallet, "portfolio": portfolio}
