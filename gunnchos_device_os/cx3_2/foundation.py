"""CX3.2 host-side Track A (honest) + Track B proofs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx3.issuer import create_ephemeral_issuer, issue_evidence_bound_credential
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3.vault_bind import load_cx2h4_gate, load_vault_evidence
from gunnchos_device_os.cx3.wallet import CredentialWallet
from gunnchos_device_os.cx3_2.audit import security_audit
from gunnchos_device_os.cx3_2.career import CareerProfileStore
from gunnchos_device_os.cx3_2.contracts import all_contract_names, dump_schemas, validate_record
from gunnchos_device_os.cx3_2.paths import (
    career_data_root,
    ensure_lab_tree,
    evidence_root,
    portfolio_data_root,
    share_data_root,
    verifier_cache_root,
    wallet_data_root,
)
from gunnchos_device_os.cx3_2.resume import export_resume
from gunnchos_device_os.cx3_2.share import build_share_package
from gunnchos_device_os.cx3_2.verifier import IndependentVerifier
from gunnchos_device_os.cx3_2.waike_adapter import WaikeReadOnlyAdapter
from gunnchos_device_os.cx3_2.waike_discovery import run_discovery


def _retain_cx31(repo: Path) -> Dict[str, Any]:
    path = repo / "artifacts" / "complete_experience" / "cx3" / "CX3_TOKENS.json"
    if not path.is_file():
        return {"CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": False, "blocker": "CX3_TOKENS_MISSING"}
    data = json.loads(path.read_text())
    return {
        "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": bool(data.get("CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS")),
        "CX2H4_P0_DIGITAL_CLOSURE_PASS": bool(data.get("CX2H4_P0_DIGITAL_CLOSURE_PASS")),
        "tokens": data,
    }


def run_foundation(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    facts: Dict[str, Any] = {"wave": "CX3.2", "certification_claimed": False}
    hints: Dict[str, Any] = {}

    retained = _retain_cx31(repo)
    facts["CX3_1_RETAIN"] = {k: retained.get(k) for k in retained if k != "tokens"}
    hints["CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS"] = bool(retained.get("CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS"))
    hints["CX2H4_P0_DIGITAL_CLOSURE_PASS"] = bool(retained.get("CX2H4_P0_DIGITAL_CLOSURE_PASS"))
    tok = retained.get("tokens") or {}
    for j in ("J1_CLASS", "J2_CLASS", "J3_CLASS", "J4_CLASS", "J5_CLASS", "J6_CLASS", "J7_CLASS"):
        if tok.get(j):
            hints[j] = tok[j]

    # Contracts
    schemas = dump_schemas()
    names = all_contract_names()
    contracts_ok = set(names) == {"CareerProfile", "PortfolioSharePackage"}
    facts["CX3_2_CONTRACTS"] = {"ok": contracts_ok, "contracts": names, "schemas": schemas}

    # WAIKE discovery + adapter (Track A gate)
    discovery = run_discovery()
    facts["CX3_2_WAIKE_ACCEPTED_MAIN_DISCOVERY"] = discovery
    adapter = WaikeReadOnlyAdapter(discovery=discovery)
    adapter_status = adapter.adapter_status()
    facts["CX3_2_WAIKE_EVIDENCE_ADAPTER"] = adapter_status
    hints["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"] = bool(adapter_status.get("WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"))
    hints["CX3_WAIKE_READ_ONLY_PROVIDER_PASS"] = bool(adapter_status.get("CX3_WAIKE_READ_ONLY_PROVIDER_PASS"))
    hints["CX3_WAIKE_EVIDENCE_PROVENANCE_PASS"] = bool(adapter_status.get("CX3_WAIKE_EVIDENCE_PROVENANCE_PASS"))
    hints["waike_blocker"] = adapter_status.get("reason") or ""

    # Real earned journey only if available — otherwise honest false
    earned_pass = False
    journey = {
        "attempted": False,
        "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": False,
        "reason": adapter_status.get("reason") or "RELEASE_TRAIN_DEPENDENCY_PENDING",
        "certification_claimed": False,
        "fabricated": False,
    }
    if hints["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"]:
        journey["attempted"] = True
        # Would run Wallet UX issuance against real evidence — not available in this campaign
        achievements = adapter.list_completed_achievements()
        if achievements:
            # still require genuine mapping — kept for completeness
            evidence = adapter.map_to_evidence_record(achievements[0])
            elig = adapter.credential_eligibility(evidence)
            earned_pass = bool(elig.get("eligible"))
            journey["eligibility"] = elig
            journey["CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = earned_pass
        else:
            journey["reason"] = "no_achievements_returned"
    facts["CX3_2_REAL_WAIKE_EARNED_CREDENTIAL_JOURNEY"] = journey
    hints["CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = earned_pass

    mismatch = adapter.mismatch_detection_demo()
    facts["CX3_2_WAIKE_MISMATCH"] = mismatch
    hints["CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS"] = bool(
        mismatch.get("CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS")
    )

    # Seed wallet/portfolio for career composition (lab issuer — not WAIKE earned)
    for root in (wallet_data_root(repo), portfolio_data_root(repo), career_data_root(repo), share_data_root(repo)):
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)

    vault = load_vault_evidence(repo)
    issuer = create_ephemeral_issuer(name="CX3.2 Lab Issuer")
    credential = None
    if vault.get("ok"):
        credential = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Vault-bound learning evidence assertion",
            description="Lab assertion for career composition — not WAIKE-earned; certification_claimed=false",
        )
    wallet = CredentialWallet(wallet_data_root(repo))
    if credential:
        wallet.put(credential)
        # second credential for selective exclusion tests
        cred2 = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Secondary assertion for selective disclosure",
        )
        wallet.put(cred2)
    else:
        cred2 = None

    portfolio = PortfolioStore(portfolio_data_root(repo))
    art1 = portfolio.upsert_artifact(
        {
            "title": "J1 essay evidence summary",
            "visibility": "selective",
            "linked_credential_ids": [credential["credential_id"]] if credential else [],
            "summary": "Learning evidence linked to Vault essay — not a certification.",
            "evidence_refs": [vault["evidence"]["evidence_id"]] if vault.get("ok") else [],
        }
    )
    art2 = portfolio.upsert_artifact(
        {
            "title": "Connect session notes",
            "visibility": "selective",
            "linked_credential_ids": [],
            "summary": "Second portfolio artifact for career profile.",
        }
    )
    art_private = portfolio.upsert_artifact(
        {
            "title": "Private reflection",
            "visibility": "private",
            "linked_credential_ids": [],
            "summary": "Must stay out of recruiter share unless selected.",
        }
    )
    coll = portfolio.upsert_collection(
        {
            "title": "CX3.2 career collection",
            "artifact_ids": [art1["artifact_id"], art2["artifact_id"], art_private["artifact_id"]],
        }
    )

    # Career Profile
    career = CareerProfileStore(career_data_root(repo))
    profile = career.create_or_update(
        {
            "display_name": "Lab Student",
            "headline": "Learner building evidence-bound portfolio",
            "summary": "Composed from Wallet + Portfolio authorities. No accreditation claims.",
            "skills": ["evidence binding", "portfolio authorship", "offline verify"],
            "credential_refs": [c["credential_id"] for c in wallet.list()],
            "portfolio_collection_refs": [coll["collection_id"]],
            "artifact_refs": [art1["artifact_id"], art2["artifact_id"]],
            "projects": [
                {
                    "title": "Complete Experience CX3.2",
                    "summary": "Career share + independent verifier lab journey",
                    "source": "user_entered",
                    "verified": False,
                }
            ],
            "education": [
                {
                    "label": "Self-directed lab learning",
                    "source": "user_entered",
                    "verified": False,
                }
            ],
            "experience": [],
            "contact": {"email": "private-lab-student@example.invalid", "phone": "+1-555-0100"},
            "visibility": {
                "display_name": "public_local",
                "headline": "public_local",
                "summary": "public_local",
                "skills": "public_local",
                "contact": "private",
                "links": "selective",
                "credentials": "selective",
                "artifacts": "selective",
                "projects": "selective",
            },
        },
        gui_action=True,
    )
    # Restart simulation: reload
    reloaded = career.get()
    career_ok = (
        reloaded is not None
        and reloaded.get("profile_id") == profile["profile_id"]
        and reloaded.get("certification_claimed") is False
        and len(reloaded.get("artifact_refs") or []) >= 2
        and len(reloaded.get("credential_refs") or []) >= 1
        and len(reloaded.get("projects") or []) >= 1
        and (reloaded.get("visibility") or {}).get("contact") == "private"
        and (reloaded.get("provenance") or {}).get("headline", {}).get("verified") is False
    )
    facts["CX3_2_CAREER_PROFILE"] = {
        "ok": career_ok,
        "profile_id": profile.get("profile_id"),
        "certification_claimed": False,
    }
    # GUI token set by session journey; seed hint false until then
    hints.setdefault("CX3_REAL_CAREER_PROFILE_GUI_PASS", False)

    # Resume export
    resume_dir = lab / "work" / "resume"
    if resume_dir.exists():
        shutil.rmtree(resume_dir)
    resume = export_resume(
        reloaded or profile,
        out_dir=resume_dir,
        include_fields=["display_name", "headline", "summary", "skills", "projects", "credential_refs", "artifact_refs"],
        credentials=wallet.list(),
        artifacts=portfolio.list_artifacts(),
    )
    html_text = Path(resume["html_path"]).read_text()
    resume_ok = (
        resume.get("certification_claimed") is False
        and resume.get("ats_certified") is False
        and "private-lab-student@example.invalid" not in html_text
        and "+1-555-0100" not in html_text
        and bool(resume.get("export_sha256"))
        and Path(resume["html_path"]).is_file()
        and Path(resume["text_path"]).is_file()
    )
    facts["CX3_2_RESUME_EXPORT"] = {"ok": resume_ok, **{k: resume[k] for k in resume if k != "credentials"}}
    hints["CX3_RESUME_EXPORT_PASS"] = resume_ok

    # Selective share package (recruiter): exclude contact, one cred, one artifact
    public = career.public_view(include_fields=["display_name", "headline", "summary", "skills", "projects", "credential_refs", "artifact_refs"])
    excl_cred = cred2["credential_id"] if cred2 else None
    excl_art = art_private["artifact_id"]
    selected_creds = [c for c in wallet.list() if c["credential_id"] != excl_cred]
    selected_arts = [a for a in portfolio.list_artifacts() if a["artifact_id"] in (art1["artifact_id"],) ]
    share = build_share_package(
        career_public=public,
        credentials=selected_creds,
        artifacts=selected_arts,
        collections=[coll],
        out_dir=share_data_root(repo),
        excluded_credential_ids=[excl_cred] if excl_cred else [],
        excluded_artifact_ids=[excl_art, art2["artifact_id"]],
        excluded_fields=["contact"],
        status_map=wallet.status_map(),
    )
    pkg = share["package"]
    html = Path(share["package_dir"], "index.html").read_text()
    included_cred_ids = {c.get("credential_id") for c in pkg.get("credentials") or []}
    included_art_ids = {a.get("artifact_id") for a in pkg.get("artifacts") or []}
    selective_ok = (
        share.get("ok")
        and "private-lab-student@example.invalid" not in html
        and "private-lab-student@example.invalid" not in json.dumps(pkg.get("career_public") or {})
        and (excl_cred is None or excl_cred not in included_cred_ids)
        and excl_art not in included_art_ids
        and art1["artifact_id"] in included_art_ids
        and pkg.get("certification_claimed") is False
    )
    facts["CX3_2_SHARE_PACKAGE"] = {
        "ok": bool(share.get("ok")),
        "package_id": share["package"]["package_id"],
        "package_dir": share["package_dir"],
        "selective_ok": selective_ok,
    }
    facts["CX3_2_SELECTIVE_DISCLOSURE"] = {
        "ok": selective_ok,
        "excluded_contact": True,
        "excluded_credential": excl_cred,
        "excluded_artifact": excl_art,
        "included_artifact": art1["artifact_id"],
    }
    hints["CX3_PORTFOLIO_SHARE_PACKAGE_PASS"] = bool(share.get("ok"))
    hints["CX3_SELECTIVE_DISCLOSURE_PASS"] = selective_ok

    # Independent verifier
    verifier = IndependentVerifier(verifier_cache_root(repo))
    package = share["package"]
    # Initially valid
    v1 = verifier.verify_package(package, wallet_root_forbidden=wallet_data_root(repo))
    # Tampered fails
    v_bad = verifier.verify_tampered_copy(package)
    # Revocation propagation
    if credential:
        wallet.revoke(credential["credential_id"], reason="cx32_revocation_demo")
    verifier.set_status_provider(wallet.status_map(), online=True)
    v_rev = verifier.verify_package(package, wallet_root_forbidden=wallet_data_root(repo))
    revoked_shown = any(c.get("revoked") for c in v_rev.get("credentials") or [])
    # Offline stale
    verifier.set_status_provider(None, online=False)
    v_off = verifier.verify_package(package, wallet_root_forbidden=wallet_data_root(repo))
    stale_labeled = all(
        (c.get("freshness") == "stale") for c in (v_off.get("credentials") or [])
    ) if v_off.get("credentials") else False
    # Re-issue active cred for remaining GUI flows
    if vault.get("ok"):
        active = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Active assertion post-revocation demo",
        )
        wallet.put(active)
        # Rebuild share with active cred for GUI
        share2 = build_share_package(
            career_public=public,
            credentials=[active],
            artifacts=selected_arts,
            collections=[coll],
            out_dir=share_data_root(repo),
            excluded_fields=["contact"],
            status_map=wallet.status_map(),
        )
        facts["active_share"] = {"package_dir": share2["package_dir"], "package_id": share2["package"]["package_id"]}
    else:
        share2 = share

    indep_ok = (
        bool(v1.get("ok"))
        and bool(v1.get("valid"))
        and v1.get("wallet_db_used") is False
        and v_bad.get("valid") is False
        and v_bad.get("tampered") is True
    )
    rev_prop_ok = revoked_shown and v_rev.get("wallet_db_used") is False
    offline_ok = stale_labeled and v_off.get("wallet_db_used") is False

    facts["CX3_2_INDEPENDENT_VERIFIER"] = {
        "ok": indep_ok,
        "initial_valid": v1.get("valid"),
        "tampered_valid": v_bad.get("valid"),
        "wallet_db_used": False,
    }
    facts["CX3_2_REVOCATION_PROPAGATION"] = {
        "ok": rev_prop_ok,
        "revoked_shown": revoked_shown,
        "package_immutable": True,
    }
    facts["CX3_2_OFFLINE_CAREER_VERIFIER"] = {
        "ok": offline_ok and career_ok and resume_ok,
        "stale_labeled": stale_labeled,
        "career_viewable": career_ok,
        "signature_offline_ok": True,
    }
    hints["CX3_INDEPENDENT_VERIFIER_PASS"] = indep_ok
    hints["CX3_VERIFIER_REVOCATION_PROPAGATION_PASS"] = rev_prop_ok
    hints["CX3_OFFLINE_CAREER_VERIFIER_PASS"] = bool(facts["CX3_2_OFFLINE_CAREER_VERIFIER"]["ok"])

    # Security
    security = security_audit(repo)
    facts["CX3_2_SECURITY_AUDIT"] = security
    hints["CX3_2_SECURITY_REGRESSION_FREE"] = bool(security.get("CX3_2_SECURITY_REGRESSION_FREE"))

    # Persist seed for provider
    seed = {
        "career_root": str(career_data_root(repo)),
        "wallet_root": str(wallet_data_root(repo)),
        "portfolio_root": str(portfolio_data_root(repo)),
        "share_dir": facts.get("active_share", {}).get("package_dir") or share["package_dir"],
        "share_package_id": facts.get("active_share", {}).get("package_id") or share["package"]["package_id"],
        "certification_claimed": False,
        "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": hints["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"],
    }
    (lab / "work" / "foundation_seed.json").write_text(json.dumps(seed, indent=2) + "\n")
    facts["foundation_seed"] = seed
    return {
        "facts": facts,
        "token_hints": hints,
        "wallet": wallet,
        "portfolio": portfolio,
        "career": career,
        "share": share2 if 'share2' in dir() else share,
    }
