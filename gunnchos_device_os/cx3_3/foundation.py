"""CX3.3 foundation orchestration — rebind, WAIKE gate, education/career digital closure."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx3.issuer import create_ephemeral_issuer, issue_evidence_bound_credential
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3.vault_bind import load_vault_evidence
from gunnchos_device_os.cx3.wallet import CredentialWallet
from gunnchos_device_os.cx3_2.career import CareerProfileStore
from gunnchos_device_os.cx3_2.resume import export_resume
from gunnchos_device_os.cx3_2.share import build_share_package
from gunnchos_device_os.cx3_3.a11y import run_automated_a11y
from gunnchos_device_os.cx3_3.career_package import build_career_package
from gunnchos_device_os.cx3_3.domain_matrix import build_blocker_register, build_domain_matrix, build_merge_readiness
from gunnchos_device_os.cx3_3.education import EducationTimelineStore
from gunnchos_device_os.cx3_3.paths import (
    career_data_root,
    career_package_root,
    education_data_root,
    ensure_lab_tree,
    portfolio_data_root,
    recovery_profile_root,
    share_data_root,
    skill_graph_root,
    verifier_cache_root,
    wallet_data_root,
)
from gunnchos_device_os.cx3_3.rebind import rebind_truth
from gunnchos_device_os.cx3_3.recovery import recover_from_package
from gunnchos_device_os.cx3_3.security import security_audit
from gunnchos_device_os.cx3_3.skill_graph import SkillEvidenceGraph
from gunnchos_device_os.cx3_3.verifier_matrix import run_verifier_matrix
from gunnchos_device_os.cx3_3.waike_discovery import run_release_lane_discovery


def run_foundation(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    facts: Dict[str, Any] = {"wave": "CX3.3", "certification_claimed": False}
    hints: Dict[str, Any] = {}

    # §2 Rebind
    rebind_facts, rebind_hints = rebind_truth(repo)
    facts["CX3_3_PROVENANCE_REBIND"] = rebind_facts
    hints.update(rebind_hints)

    # §3–4 WAIKE release-lane discovery + conditional Track A
    waike = run_release_lane_discovery(repo)
    facts["CX3_3_WAIKE_RELEASE_DEPENDENCY_DISCOVERY"] = waike
    facts["CX3_3_REAL_WAIKE_EARNED_CREDENTIAL"] = waike.get("earned_credential_journey") or {}
    hints["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"] = bool(waike.get("WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"))
    hints["CX3_WAIKE_READ_ONLY_PROVIDER_PASS"] = bool(waike.get("CX3_WAIKE_READ_ONLY_PROVIDER_PASS"))
    hints["CX3_WAIKE_EVIDENCE_PROVENANCE_PASS"] = bool(waike.get("CX3_WAIKE_EVIDENCE_PROVENANCE_PASS"))
    hints["CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS"] = bool(
        waike.get("CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS")
    )
    hints["CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] = bool(
        (waike.get("earned_credential_journey") or {}).get("CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS")
    )
    hints["waike_blocker"] = waike.get("reason") or ""

    # Reset lab work dirs
    for root in (
        wallet_data_root(repo),
        portfolio_data_root(repo),
        career_data_root(repo),
        share_data_root(repo),
        education_data_root(repo),
        skill_graph_root(repo),
        career_package_root(repo),
    ):
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)

    vault = load_vault_evidence(repo)
    issuer = create_ephemeral_issuer(name="CX3.3 Lab Issuer")
    credential = None
    if vault.get("ok"):
        credential = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Vault-bound learning evidence assertion",
            description="Lab assertion for education/career closure — not WAIKE-earned; certification_claimed=false",
        )

    wallet = CredentialWallet(wallet_data_root(repo))
    # Skill tags are composed separately — never mutate signed credential bodies
    skill_sidecar: Dict[str, list] = {}
    if credential:
        wallet.put(credential)
        skill_sidecar[credential["credential_id"]] = ["evidence binding", "portfolio authorship"]
        cred2 = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Secondary assertion for selective disclosure",
        )
        wallet.put(cred2)
        skill_sidecar[cred2["credential_id"]] = ["offline verify"]
    else:
        cred2 = None

    portfolio = PortfolioStore(portfolio_data_root(repo))
    art1 = portfolio.upsert_artifact(
        {
            "title": "J1 essay evidence summary",
            "visibility": "selective",
            "linked_credential_ids": [credential["credential_id"]] if credential else [],
            "summary": "Learning evidence linked to Vault essay — not a certification.",
            "skills": ["evidence binding"],
            "content_sha256": (vault.get("evidence") or {}).get("artifact_sha256") or "abc",
            "evidence_refs": [vault["evidence"]["evidence_id"]] if vault.get("ok") else [],
        }
    )
    art2 = portfolio.upsert_artifact(
        {
            "title": "Connect session notes",
            "visibility": "selective",
            "linked_credential_ids": [],
            "summary": "Second portfolio artifact.",
            "skills": ["portfolio authorship"],
            "content_sha256": "def",
        }
    )
    art_private = portfolio.upsert_artifact(
        {
            "title": "Private reflection",
            "visibility": "private",
            "linked_credential_ids": [],
            "summary": "Must stay out of package unless selected.",
            "content_sha256": "ghi",
        }
    )
    coll = portfolio.upsert_collection(
        {
            "title": "CX3.3 career collection",
            "artifact_ids": [art1["artifact_id"], art2["artifact_id"], art_private["artifact_id"]],
        }
    )

    career = CareerProfileStore(career_data_root(repo))
    profile = career.create_or_update(
        {
            "display_name": "Lab Student",
            "headline": "Learner building evidence-bound portfolio",
            "summary": "Composed from Wallet + Portfolio + Education authorities. No accreditation claims.",
            "skills": ["evidence binding", "portfolio authorship", "offline verify", "self study"],
            "credential_refs": [c["credential_id"] for c in wallet.list()],
            "portfolio_collection_refs": [coll["collection_id"]],
            "artifact_refs": [art1["artifact_id"], art2["artifact_id"]],
            "projects": [
                {
                    "title": "Complete Experience CX3.3",
                    "summary": "Education/career digital closure",
                    "source": "user_entered",
                    "verified": False,
                }
            ],
            "education": [
                {"label": "Self-directed lab learning", "source": "user_entered", "verified": False}
            ],
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

    # §5 Education timeline
    edu = EducationTimelineStore(education_data_root(repo))
    edu.create()
    if credential:
        edu.add_entry(
            {
                "label": credential.get("name") or "Credential-linked achievement",
                "kind": "achievement",
                "skills": skill_sidecar.get(credential["credential_id"], []),
                "evidence_refs": [
                    e.get("evidence_id") for e in (credential.get("evidence") or []) if isinstance(e, dict)
                ],
            },
            gui_action=True,
            verified_credential=credential,
        )
    edu.add_entry(
        {
            "label": "Community college coursework (self-reported)",
            "kind": "education",
            "source": "user_entered",
            "verified": False,
            "skills": ["self study"],
        },
        gui_action=True,
    )
    # Negative path must raise
    user_verified_rejected = False
    try:
        edu.add_entry(
            {"label": "Fake degree", "source": "user_entered", "verified": True},
            gui_action=True,
        )
    except ValueError:
        user_verified_rejected = True
    edu_doc = edu.get()
    edu_ok = (
        edu.distinguishes_verified()
        and user_verified_rejected
        and edu.offline_view().get("ok")
        and edu_doc is not None
        and edu_doc.get("certification_claimed") is False
    )
    # Restart persistence
    edu2 = EducationTimelineStore(education_data_root(repo))
    edu_ok = edu_ok and edu2.get() is not None and edu2.get().get("timeline_id") == edu_doc.get("timeline_id")
    facts["CX3_3_EDUCATION_TIMELINE"] = {
        "ok": edu_ok,
        "timeline_id": (edu_doc or {}).get("timeline_id"),
        "entry_count": len((edu_doc or {}).get("entries") or []),
        "distinguishes_verified": edu.distinguishes_verified(),
        "user_entered_verified_rejected": user_verified_rejected,
        "certification_claimed": False,
    }
    hints["CX3_EDUCATION_TIMELINE_PASS"] = edu_ok

    def _creds_with_skills(creds):
        out = []
        for c in creds:
            cc = dict(c)
            cc["skills"] = list(skill_sidecar.get(c.get("credential_id"), []))
            out.append(cc)
        return out

    # §6 Skill evidence graph
    graph_store = SkillEvidenceGraph(skill_graph_root(repo))
    graph = graph_store.build(
        credentials=_creds_with_skills(wallet.list()),
        artifacts=portfolio.list_artifacts(),
        user_skills=list(profile.get("skills") or []),
        waike_evidence=[],
    )
    # Revocation propagation on graph
    if credential:
        wallet.revoke(credential["credential_id"], reason="cx33_skill_graph_demo")
    graph_rev = graph_store.build(
        credentials=_creds_with_skills(wallet.list()),
        artifacts=portfolio.list_artifacts(),
        user_skills=list(profile.get("skills") or []),
        revoked_ids={credential["credential_id"]} if credential else set(),
    )
    explain = graph_store.explain("evidence binding")
    text_promote_blocked = False
    try:
        graph_store.promote_user_text_to_verified("self study")
    except PermissionError:
        text_promote_blocked = True
    # Restore active credential for remaining flows
    if vault.get("ok"):
        active = issue_evidence_bound_credential(
            issuer,
            subject_profile_id="profile:lab-student",
            evidence=vault["evidence"],
            name="Active assertion post skill-graph revocation demo",
        )
        wallet.put(active)
        skill_sidecar[active["credential_id"]] = ["evidence binding", "portfolio authorship"]
        credential = active
        graph = graph_store.build(
            credentials=_creds_with_skills(wallet.list()),
            artifacts=portfolio.list_artifacts(),
            user_skills=list(profile.get("skills") or []),
        )

    skills = graph.get("skills") or []
    has_verified = any(s.get("verified") and s.get("evidence_backed") for s in skills)
    has_self = any(s.get("self_declared") and not s.get("verified") for s in skills)
    rev_reflected = any(s.get("status") == "revoked_dependency" for s in (graph_rev.get("skills") or []))
    skill_ok = (
        has_verified
        and has_self
        and text_promote_blocked
        and rev_reflected
        and bool(explain.get("ok"))
        and graph.get("certification_claimed") is False
    )
    facts["CX3_3_SKILL_EVIDENCE_GRAPH"] = {
        "ok": skill_ok,
        "graph_id": graph.get("graph_id"),
        "skill_count": len(skills),
        "explain": explain,
        "revocation_reflected": rev_reflected,
        "text_promote_blocked": text_promote_blocked,
        "certification_claimed": False,
    }
    hints["CX3_SKILL_EVIDENCE_GRAPH_PASS"] = skill_ok

    # Resume + share (retained capability, fresh in cx3_3 lab)
    resume_dir = lab / "work" / "resume"
    if resume_dir.exists():
        shutil.rmtree(resume_dir)
    public = career.public_view(
        include_fields=["display_name", "headline", "summary", "skills", "projects", "credential_refs", "artifact_refs"]
    )
    resume = export_resume(
        career.get() or profile,
        out_dir=resume_dir,
        include_fields=["display_name", "headline", "summary", "skills", "projects", "credential_refs", "artifact_refs"],
        credentials=wallet.list(),
        artifacts=portfolio.list_artifacts(),
    )
    selected_arts = [a for a in portfolio.list_artifacts() if a["artifact_id"] == art1["artifact_id"]]
    share = build_share_package(
        career_public=public,
        credentials=wallet.list(),
        artifacts=selected_arts,
        collections=[coll],
        out_dir=share_data_root(repo),
        excluded_fields=["contact"],
        excluded_artifact_ids=[art_private["artifact_id"], art2["artifact_id"]],
        status_map=wallet.status_map(),
    )

    # §7 Career package
    pkg = build_career_package(
        out_dir=career_package_root(repo),
        career_public=public,
        resume_meta=resume,
        credentials=wallet.list(),
        artifacts=selected_arts,
        education_timeline=edu.get(),
        skill_graph=graph_store.get(),
        verifier_metadata={"independent": True, "wallet_db_used": False},
        privacy_manifest={
            "excluded_fields": ["contact"],
            "no_hidden_private_fields": True,
            "no_local_path_leakage": True,
            "certification_claimed": False,
        },
        excluded_fields=["contact"],
    )
    facts["CX3_3_CAREER_PACKAGE"] = {
        "ok": bool(pkg.get("ok")),
        "package_id": pkg.get("package_id"),
        "package_dir": pkg.get("package_dir"),
        "content_sha256": pkg.get("content_sha256"),
        "privacy_leak": pkg.get("privacy_leak"),
        "certification_claimed": False,
    }
    hints["CX3_CAREER_PACKAGE_PASS"] = bool(pkg.get("ok"))

    # §8 Clean-profile recovery
    recovery = recover_from_package(
        Path(pkg["package_dir"]),
        dest_root=recovery_profile_root(repo),
        verifier_cache=verifier_cache_root(repo) / "recovery",
    )
    facts["CX3_3_CAREER_PACKAGE_RECOVERY"] = recovery
    hints["CX3_CAREER_PACKAGE_RECOVERY_PASS"] = bool(recovery.get("CX3_CAREER_PACKAGE_RECOVERY_PASS"))

    # §9 Verifier matrix
    matrix = run_verifier_matrix(lab / "work" / "verifier_matrix")
    facts["CX3_3_VERIFIER_MATRIX"] = matrix
    hints["CX3_VERIFIER_MATRIX_PASS"] = bool(matrix.get("CX3_VERIFIER_MATRIX_PASS"))

    # §10 Automated a11y
    a11y = run_automated_a11y(repo)
    facts["CX3_3_AUTOMATED_A11Y"] = a11y
    hints["CX3_AUTOMATED_A11Y_PASS"] = bool(a11y.get("CX3_AUTOMATED_A11Y_PASS"))
    hints["J6_CLASS"] = "HUMAN_VALIDATION_PENDING"

    # §12 Security
    security = security_audit(repo)
    facts["CX3_3_SECURITY_AUDIT"] = security
    hints["CX3_3_SECURITY_REGRESSION_FREE"] = bool(security.get("CX3_3_SECURITY_REGRESSION_FREE"))

    seed = {
        "career_root": str(career_data_root(repo)),
        "wallet_root": str(wallet_data_root(repo)),
        "portfolio_root": str(portfolio_data_root(repo)),
        "education_root": str(education_data_root(repo)),
        "skill_graph_root": str(skill_graph_root(repo)),
        "share_dir": share["package_dir"],
        "career_package_dir": pkg.get("package_dir"),
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
        "education": edu,
        "skill_graph": graph_store,
        "career_package": pkg,
        "share": share,
    }


def finalize_matrices(repo: Path, tokens_dict: Dict[str, Any]) -> Dict[str, Any]:
    tip = tokens_dict.get("_tip") or "unknown"
    try:
        import subprocess

        tip = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        pass
    return {
        "CX3_3_EDUCATION_CAREER_DOMAIN_MATRIX": build_domain_matrix(tokens_dict, tip),
        "CX3_3_BLOCKER_REGISTER": build_blocker_register(tokens_dict),
        "CX3_3_CX_STACK_MERGE_READINESS": build_merge_readiness(repo),
    }
