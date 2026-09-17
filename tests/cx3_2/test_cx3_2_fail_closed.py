"""Fail-closed CX3.2 tests — career/verifier + honest WAIKE gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.cx3.issuer import create_ephemeral_issuer, issue_evidence_bound_credential
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3.wallet import CredentialWallet
from gunnchos_device_os.cx3_2.audit import pick_next_gate, security_audit
from gunnchos_device_os.cx3_2.career import CareerProfileStore
from gunnchos_device_os.cx3_2.contracts import all_contract_names, validate_record
from gunnchos_device_os.cx3_2.resume import export_resume
from gunnchos_device_os.cx3_2.share import build_share_package
from gunnchos_device_os.cx3_2.tokens import Cx32Tokens
from gunnchos_device_os.cx3_2.verifier import IndependentVerifier
from gunnchos_device_os.cx3_2.waike_adapter import WaikeReadOnlyAdapter
from gunnchos_device_os.cx3_2.waike_discovery import run_discovery

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


def test_contracts_include_career_and_share():
    assert set(all_contract_names()) == {"CareerProfile", "PortfolioSharePackage"}


def test_career_gui_cannot_create_verified_claims(tmp_path):
    store = CareerProfileStore(tmp_path / "career")
    with pytest.raises(ValueError):
        store.create_or_update(
            {
                "education": [{"label": "Fake degree", "source": "user_entered", "verified": True}],
            },
            gui_action=True,
        )


def test_resume_excludes_private_contact(tmp_path):
    store = CareerProfileStore(tmp_path / "career")
    profile = store.create_or_update(
        {
            "display_name": "Lab Student",
            "headline": "Headline",
            "summary": "Summary",
            "skills": ["a"],
            "contact": {"email": "secret@example.invalid"},
            "visibility": {"contact": "private", "display_name": "public_local", "headline": "public_local", "summary": "public_local", "skills": "public_local"},
        },
        gui_action=True,
    )
    meta = export_resume(profile, out_dir=tmp_path / "resume", include_fields=["display_name", "headline", "summary", "skills", "contact"])
    html = Path(meta["html_path"]).read_text()
    assert "secret@example.invalid" not in html
    assert meta["certification_claimed"] is False
    assert meta["ats_certified"] is False


def test_share_excludes_non_selected(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    c1 = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence(), name="keep")
    c2 = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence(), name="drop")
    portfolio = PortfolioStore(tmp_path / "portfolio")
    a1 = portfolio.upsert_artifact({"title": "keep", "visibility": "selective", "linked_credential_ids": []})
    a2 = portfolio.upsert_artifact({"title": "drop", "visibility": "private", "linked_credential_ids": []})
    result = build_share_package(
        career_public={"display_name": "Lab", "certification_claimed": False, "contact": {"email": "x@y.z"}},
        credentials=[c1],
        artifacts=[a1],
        out_dir=tmp_path / "share",
        excluded_credential_ids=[c2["credential_id"]],
        excluded_artifact_ids=[a2["artifact_id"]],
        excluded_fields=["contact"],
    )
    package = result["package"]
    included_ids = {c["credential_id"] for c in package["credentials"]}
    included_arts = {a["artifact_id"] for a in package["artifacts"]}
    html = Path(result["package_dir"], "index.html").read_text()
    assert c2["credential_id"] not in included_ids
    assert a2["artifact_id"] not in included_arts
    assert "x@y.z" not in html
    assert "x@y.z" not in json.dumps(package.get("career_public"))
    assert c1["credential_id"] in included_ids


def test_verifier_no_wallet_db_and_tamper_fail(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence())
    share = build_share_package(
        career_public={"display_name": "Lab", "certification_claimed": False},
        credentials=[cred],
        artifacts=[],
        out_dir=tmp_path / "share",
        excluded_fields=["contact"],
    )
    v = IndependentVerifier(tmp_path / "vcache")
    wallet_root = tmp_path / "wallet"
    wallet_root.mkdir()
    good = v.verify_package(share["package"], wallet_root_forbidden=wallet_root)
    bad = v.verify_tampered_copy(share["package"])
    assert good["valid"] is True
    assert good["wallet_db_used"] is False
    assert bad["valid"] is False
    assert bad["tampered"] is True


def test_revoked_not_valid_and_stale_labeled(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(issuer, subject_profile_id="p", evidence=_evidence())
    wallet = CredentialWallet(tmp_path / "wallet")
    wallet.put(cred)
    share = build_share_package(
        career_public={"display_name": "Lab", "certification_claimed": False},
        credentials=[cred],
        artifacts=[],
        out_dir=tmp_path / "share",
        status_map=wallet.status_map(),
    )
    v = IndependentVerifier(tmp_path / "vcache")
    wallet.revoke(cred["credential_id"])
    v.set_status_provider(wallet.status_map(), online=True)
    online = v.verify_package(share["package"])
    assert any(c.get("revoked") for c in online["credentials"])
    assert online["valid"] is False
    v.set_status_provider(None, online=False)
    offline = v.verify_package(share["package"])
    assert all(c.get("freshness") == "stale" for c in offline["credentials"])


def test_waike_adapter_rejects_mutation_and_no_fake_pass():
    discovery = run_discovery()
    adapter = WaikeReadOnlyAdapter(discovery=discovery)
    with pytest.raises(PermissionError):
        adapter.mutate("create_completion")
    status = adapter.adapter_status()
    assert status["CX3_WAIKE_READ_ONLY_PROVIDER_PASS"] is True
    # Earn PASS only with genuine evidence — currently release-blocked
    assert status["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"] is False
    journey_gate = adapter.evidence_availability_gate()
    assert journey_gate["WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"] is False


def test_mismatch_detection_on_fixture():
    adapter = WaikeReadOnlyAdapter(discovery={"can_expose_real_completed_learning_evidence_readonly": False})
    result = adapter.mismatch_detection_demo()
    assert result["CX3_WAIKE_EVIDENCE_MISMATCH_DETECTION_PASS"] is True
    assert result["authoritative_waike_mutated"] is False


def test_next_gate_rules():
    assert pick_next_gate({"CX3_2_CAREER_VERIFIER_PASS": True, "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": True}) == (
        "CX3_3_EDUCATION_CAREER_DIGITAL_CLOSURE_AUDIT"
    )
    assert pick_next_gate({"CX3_2_CAREER_VERIFIER_PASS": True, "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": False}) == (
        "CX3_2B_WAIKE_RELEASE_DEPENDENCY_RETRY"
    )
    assert pick_next_gate({"CX3_2_CAREER_VERIFIER_PASS": False, "lab_blocker": "RESUME"}).startswith("CX3_2B_")


def test_security_audit_clean():
    result = security_audit(ROOT)
    assert result["CX3_2_SECURITY_REGRESSION_FREE"] is True
    assert result["certification_claimed"] is False


def test_direct_json_edit_not_gui_action(tmp_path):
    store = CareerProfileStore(tmp_path / "career")
    profile = store.create_or_update({"headline": "from-gui"}, gui_action=True)
    assert profile["provenance"]["headline"]["gui_action"] is True
    # Direct file edit is distinguishable from GUI action provenance
    raw = json.loads((tmp_path / "career" / "career_profile.json").read_text())
    raw["headline"] = "edited-on-disk"
    raw["provenance"]["headline"]["gui_action"] = False
    (tmp_path / "career" / "career_profile.json").write_text(json.dumps(raw))
    loaded = store.get()
    assert loaded["provenance"]["headline"]["gui_action"] is False


def test_tokens_never_full_complete():
    t = Cx32Tokens()
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert t.CX3_CERTIFICATION_CLAIMED is False
