"""Fail-closed CX3.1 tests — no fake accreditation; WAIKE earned not invented."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.cx3.adapters import roundtrip_ok, to_ob3_inspired
from gunnchos_device_os.cx3.audit import pick_next_gate, security_fail_closed_audit
from gunnchos_device_os.cx3.contracts import all_contract_names, validate_record
from gunnchos_device_os.cx3.issuer import (
    create_ephemeral_issuer,
    detect_tamper,
    issue_evidence_bound_credential,
    verify_credential,
)
from gunnchos_device_os.cx3.learning_evidence import LearningEvidenceProvider
from gunnchos_device_os.cx3.portfolio import PortfolioStore
from gunnchos_device_os.cx3.tokens import Cx3Tokens
from gunnchos_device_os.cx3.wallet import CredentialWallet

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


def test_contracts_v1_present_and_claim_false():
    names = set(all_contract_names())
    assert names == {
        "CredentialRecord",
        "EvidenceRecord",
        "IssuerProfile",
        "CredentialStatus",
        "PortfolioArtifact",
        "PortfolioCollection",
        "CredentialExport",
        "PortfolioExport",
    }


def test_issuer_ephemeral_and_verify_offline(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(
        issuer, subject_profile_id="profile:t", evidence=_evidence()
    )
    assert cred["certification_claimed"] is False
    assert verify_credential(cred)["verified"] is True


def test_tamper_detected(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(
        issuer, subject_profile_id="profile:t", evidence=_evidence()
    )
    assert detect_tamper(cred)["tamper_detected"] is True


def test_revocation_fail_closed(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(
        issuer, subject_profile_id="profile:t", evidence=_evidence()
    )
    wallet = CredentialWallet(tmp_path / "wallet")
    wallet.put(cred)
    wallet.revoke(cred["credential_id"])
    result = wallet.verify(cred["credential_id"])
    assert result["verified"] is False
    assert result["revoked"] is True


def test_wallet_rejects_certification_claimed(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(
        issuer, subject_profile_id="profile:t", evidence=_evidence()
    )
    cred["certification_claimed"] = True
    wallet = CredentialWallet(tmp_path / "wallet")
    with pytest.raises(ValueError):
        wallet.put(cred)


def test_import_export_roundtrip(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(
        issuer, subject_profile_id="profile:t", evidence=_evidence()
    )
    w1 = CredentialWallet(tmp_path / "w1")
    w1.put(cred)
    export = w1.export_credentials()
    assert export["certification_claimed"] is False
    assert export["include_private_keys"] is False
    w2 = CredentialWallet(tmp_path / "w2")
    assert w2.import_credentials(export)["ok"] is True
    bad = json.loads(json.dumps(export))
    bad["certification_claimed"] = True
    assert w2.import_credentials(bad)["ok"] is False


def test_portfolio_privacy_selective_export(tmp_path):
    store = PortfolioStore(tmp_path / "portfolio")
    pub = store.upsert_artifact({"title": "public-ish", "visibility": "selective"})
    priv = store.upsert_artifact({"title": "secret", "visibility": "private"})
    result = store.selective_export([pub["artifact_id"]])
    manifest = result["export"]["manifest"]
    assert priv["artifact_id"] in manifest["skipped_private_unselected"]
    assert (Path(result["package_dir"]) / "index.html").is_file()
    assert "certification_claimed=false" in (Path(result["package_dir"]) / "index.html").read_text()


def test_ob3_clr_adapter_no_conformance_claim(tmp_path):
    issuer = create_ephemeral_issuer(store_dir=tmp_path / "issuer")
    cred = issue_evidence_bound_credential(
        issuer, subject_profile_id="profile:t", evidence=_evidence()
    )
    rt = roundtrip_ok(cred)
    assert rt["ok"] is True
    assert rt["conformance_claimed"] is False
    ob3 = to_ob3_inspired(cred)
    assert ob3["gunnchos"]["conformance_claimed"] is False
    assert ob3["gunnchos"]["certification_claimed"] is False


def test_waike_seam_true_earned_false_by_default():
    lep = LearningEvidenceProvider()
    status = lep.seam_status()
    assert status["WAIKE_INTEGRATION_SEAM_PASS"] is True
    assert status["WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] is False


def test_waike_earned_not_invented_without_honest_markers(tmp_path):
    fake = tmp_path / "fake.json"
    fake.write_text(json.dumps({"earned_credential": True, "accepted_main": False}))
    lep = LearningEvidenceProvider(waike_accepted_main_probe=fake)
    assert lep.probe_waike_earned_credential()["WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"] is False


def test_foundation_eligible_requires_gui_and_security():
    tokens = Cx3Tokens(
        CX2H4_P0_DIGITAL_CLOSURE_PASS=True,
        CX3_CONTRACTS_V1_PASS=True,
        CX3_LAB_ISSUER_ED25519_PASS=True,
        CX3_EVIDENCE_BOUND_ISSUANCE_PASS=True,
        CX3_WALLET_STORAGE_PASS=True,
        CX3_TAMPER_DETECT_PASS=True,
        CX3_REVOCATION_STATUS_PASS=True,
        CX3_OFFLINE_VERIFY_PASS=True,
        CX3_IMPORT_EXPORT_PASS=True,
        CX3_PORTFOLIO_PRIVACY_EXPORT_PASS=True,
        CX3_PORTFOLIO_PORTABLE_PACKAGE_PASS=True,
        CX3_SECURITY_FAIL_CLOSED_PASS=True,
        CX3_OB3_CLR_ADAPTER_PASS=True,
        WAIKE_INTEGRATION_SEAM_PASS=True,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J2_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J5_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J6_CLASS="HUMAN_VALIDATION_PENDING",
    )
    # missing GUI / journey
    assert tokens.foundation_eligible() is False
    tokens.CX3_WALLET_GUI_PASS = True
    tokens.CX3_PORTFOLIO_GUI_PASS = True
    tokens.CX3_SIGNED_CREDENTIAL_JOURNEY_PASS = True
    assert tokens.foundation_eligible() is True


def test_next_gate_waike_when_wallet_pass_earned_blocked():
    gate = pick_next_gate(
        {
            "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": True,
            "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": False,
        }
    )
    assert gate == "CX3_2_WAIKE_REAL_EARNED_CREDENTIAL_INTEGRATION"


def test_next_gate_career_when_waike_also_proven():
    gate = pick_next_gate(
        {
            "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": True,
            "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": True,
        }
    )
    assert gate == "CX3_2_CAREER_PORTFOLIO_SHARING_AND_VERIFIER"


def test_security_fail_closed_audit():
    result = security_fail_closed_audit(ROOT)
    assert result["CX3_SECURITY_FAIL_CLOSED_PASS"] is True
    assert result["certification_claimed"] is False


def test_validate_record_rejects_claimed_true():
    ok, errs = validate_record(
        "CredentialStatus",
        {
            "credential_id": "x",
            "status": "active",
            "updated_at": "t",
            "certification_claimed": True,
        },
    )
    assert ok is False
    assert "certification_claimed_must_be_false" in errs


def test_cx2h4_regressions_still_importable():
    from gunnchos_device_os.cx2h4.tokens import Cx2h4Tokens

    t = Cx2h4Tokens()
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert t.digital_closure_eligible() is False
