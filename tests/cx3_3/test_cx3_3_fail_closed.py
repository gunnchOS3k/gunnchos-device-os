"""Fail-closed CX3.3 tests — education/career digital closure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.cx3.issuer import create_ephemeral_issuer, issue_evidence_bound_credential
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3.wallet import CredentialWallet
from gunnchos_device_os.cx3_3.audit import pick_next_gate
from gunnchos_device_os.cx3_3.career_package import build_career_package
from gunnchos_device_os.cx3_3.domain_matrix import build_blocker_register, build_merge_readiness
from gunnchos_device_os.cx3_3.education import EducationTimelineStore
from gunnchos_device_os.cx3_3.recovery import recover_from_package
from gunnchos_device_os.cx3_3.security import security_audit
from gunnchos_device_os.cx3_3.skill_graph import SkillEvidenceGraph
from gunnchos_device_os.cx3_3.tokens import Cx33Tokens
from gunnchos_device_os.cx3_3.verifier_matrix import run_verifier_matrix

ROOT = Path(__file__).resolve().parents[2]


def _evidence():
    return {
        "evidence_id": "ev:test:1",
        "source": "vault",
        "artifact_sha256": "e72f5b8c2940c253d8dc7d7797318de2a0fa2b394f0d4caca1e6495b87e13fd6",
        "artifact_path": "cx2h2_j1_essay.odt",
        "captured_at": "2026-09-17T00:00:00Z",
        "mime": "application/vnd.oasis.opendocument.text",
        "certification_claimed": False,
    }


def test_user_entered_education_cannot_appear_verified(tmp_path):
    store = EducationTimelineStore(tmp_path / "edu")
    store.create()
    with pytest.raises(ValueError):
        store.add_entry(
            {"label": "Fake degree", "source": "user_entered", "verified": True},
            gui_action=True,
        )


def test_skill_text_entry_alone_cannot_become_verified(tmp_path):
    g = SkillEvidenceGraph(tmp_path / "sg")
    doc = g.build(credentials=[], artifacts=[], user_skills=["python"])
    skill = doc["skills"][0]
    assert skill["self_declared"] is True
    assert skill["verified"] is False
    with pytest.raises(PermissionError):
        g.promote_user_text_to_verified("python")


def test_revoked_credential_invalidates_dependent_verified_skill(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence())
    cred_view = dict(cred)
    cred_view["skills"] = ["radio"]
    g = SkillEvidenceGraph(tmp_path / "sg")
    g.build(credentials=[cred_view], artifacts=[], user_skills=[])
    revoked = g.build(
        credentials=[cred_view],
        artifacts=[],
        user_skills=[],
        revoked_ids={cred["credential_id"]},
    )
    node = next(s for s in revoked["skills"] if s["label"] == "radio")
    assert node["verified"] is False
    assert node["status"] == "revoked_dependency"


def test_missing_evidence_affects_graph_truth(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence())
    cred_view = dict(cred)
    cred_view["skills"] = ["dsp"]
    g = SkillEvidenceGraph(tmp_path / "sg")
    missing = g.build(
        credentials=[cred_view],
        artifacts=[],
        user_skills=[],
        missing_evidence_ids={"ev:test:1"},
    )
    node = next(s for s in missing["skills"] if s["label"] == "dsp")
    assert node["verified"] is False
    assert node["status"] == "missing_evidence"


def test_career_package_excludes_hidden_data(tmp_path):
    resume = {
        "export_sha256": "abc",
        "html_path": None,
        "text_path": None,
        "ats_certified": False,
    }
    # write minimal resume files
    html = tmp_path / "r.html"
    html.write_text("<html><body>Lab</body></html>")
    resume["html_path"] = str(html)
    pkg = build_career_package(
        out_dir=tmp_path / "pkg",
        career_public={
            "display_name": "Lab",
            "headline": "H",
            "contact": {"email": "private-lab-student@example.invalid"},
            "certification_claimed": False,
        },
        resume_meta=resume,
        credentials=[],
        artifacts=[],
        education_timeline={"entries": []},
        skill_graph={"skills": []},
        excluded_fields=["contact"],
    )
    assert pkg["ok"] is True
    assert "private-lab-student@example.invalid" not in json.dumps(pkg["manifest"])
    assert "contact" not in (pkg["manifest"].get("career_profile") or {})


def test_clean_profile_recovery_cannot_use_db_copy(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence())
    html = tmp_path / "r.html"
    html.write_text("<html><body>Lab</body></html>")
    pkg = build_career_package(
        out_dir=tmp_path / "pkg",
        career_public={"display_name": "Lab", "headline": "H", "skills": ["a"], "certification_claimed": False},
        resume_meta={"export_sha256": "x", "html_path": str(html), "ats_certified": False},
        credentials=[cred],
        artifacts=[{"artifact_id": "art:1", "title": "A", "visibility": "selective", "content_sha256": "abc"}],
        education_timeline={"entries": []},
        skill_graph={"skills": []},
        excluded_fields=["contact"],
    )
    result = recover_from_package(
        Path(pkg["package_dir"]),
        dest_root=tmp_path / "clean",
        verifier_cache=tmp_path / "vcache",
    )
    assert result["db_copy_used"] is False
    assert result["CX3_CAREER_PACKAGE_RECOVERY_PASS"] is True


def test_verifier_matrix_catches_negative_cases(tmp_path):
    result = run_verifier_matrix(tmp_path / "matrix")
    assert result["CX3_VERIFIER_MATRIX_PASS"] is True
    names = {c["case"] for c in result["cases"]}
    for required in (
        "valid_credential",
        "revoked_credential",
        "tampered_credential",
        "unknown_issuer",
        "stale_offline_status",
        "missing_evidence",
        "mismatched_artifact_hash",
        "selectively_disclosed_package",
    ):
        assert required in names


def test_waike_false_not_silently_promoted_by_generic_closure():
    t = Cx33Tokens(
        CX3_3_REBIND_PASS=True,
        CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS=True,
        CX3_2_CAREER_VERIFIER_PASS=True,
        CX3_EDUCATION_TIMELINE_PASS=True,
        CX3_SKILL_EVIDENCE_GRAPH_PASS=True,
        CX3_CAREER_PACKAGE_PASS=True,
        CX3_CAREER_PACKAGE_RECOVERY_PASS=True,
        CX3_VERIFIER_MATRIX_PASS=True,
        CX3_AUTOMATED_A11Y_PASS=True,
        CX3_NO_SECOND_COMPUTER_FINAL_PASS=True,
        CX3_3_SECURITY_REGRESSION_FREE=True,
        CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS=False,
        WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE=False,
    )
    assert t.digital_closure_eligible() is True
    assert t.CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS is False
    assert pick_next_gate({**t.to_dict(), "CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS": True}) == (
        "CX3_WAIKE_RELEASE_DEPENDENCY_WAIT"
    )


def test_release_dependency_not_misclassified_as_generic_pass():
    reg = build_blocker_register(
        {
            "CX3_3_REBIND_PASS": True,
            "CX3_EDUCATION_TIMELINE_PASS": True,
            "CX3_SKILL_EVIDENCE_GRAPH_PASS": True,
            "CX3_CAREER_PACKAGE_PASS": True,
            "CX3_CAREER_PACKAGE_RECOVERY_PASS": True,
            "CX3_VERIFIER_MATRIX_PASS": True,
            "CX3_AUTOMATED_A11Y_PASS": True,
            "CX3_NO_SECOND_COMPUTER_FINAL_PASS": True,
            "CX3_3_SECURITY_REGRESSION_FREE": True,
            "CX3_2_CAREER_VERIFIER_PASS": True,
            "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": True,
            "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": False,
            "waike_blocker": "RELEASE_TRAIN_DEPENDENCY_PENDING",
        }
    )
    assert reg["automatable_digital_count"] == 0
    assert any(b["id"] == "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS" for b in reg["B_release_dependency"])


def test_human_pending_not_converted_to_digital_pass():
    t = Cx33Tokens(CX3_AUTOMATED_A11Y_PASS=True, J6_CLASS="HUMAN_VALIDATION_PENDING")
    assert t.J6_CLASS == "HUMAN_VALIDATION_PENDING"
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False


def test_automatable_blocker_prevents_cx3_closure():
    t = Cx33Tokens(
        CX3_3_REBIND_PASS=True,
        CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS=True,
        CX3_2_CAREER_VERIFIER_PASS=True,
        CX3_EDUCATION_TIMELINE_PASS=False,
        CX3_SKILL_EVIDENCE_GRAPH_PASS=True,
        CX3_CAREER_PACKAGE_PASS=True,
        CX3_CAREER_PACKAGE_RECOVERY_PASS=True,
        CX3_VERIFIER_MATRIX_PASS=True,
        CX3_AUTOMATED_A11Y_PASS=True,
        CX3_NO_SECOND_COMPUTER_FINAL_PASS=True,
        CX3_3_SECURITY_REGRESSION_FREE=True,
        lab_blocker="CX3_EDUCATION_TIMELINE",
    )
    assert t.digital_closure_eligible() is False
    assert pick_next_gate({**t.to_dict(), "CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS": False}).startswith(
        "CX3_3B_"
    )


def test_merge_readiness_plan_does_not_merge():
    plan = build_merge_readiness(ROOT)
    assert plan["plan_only"] is True
    assert plan["merges_executed"] is False
    assert all(item.get("no_merge_executed") for item in plan["device_os_stack"])


def test_security_audit_clean():
    result = security_audit(ROOT)
    assert result["CX3_3_SECURITY_REGRESSION_FREE"] is True
    assert result["certification_claimed"] is False


def test_tokens_never_full_complete():
    t = Cx33Tokens()
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert t.CX3_CERTIFICATION_CLAIMED is False
