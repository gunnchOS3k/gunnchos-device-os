"""Fail-closed CX4.2 Validation Center pilot-readiness tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.cx4_validation_center.eligibility import (
    ValidationEvidenceEligibility,
    normalize_eligibility,
)
from gunnchos_device_os.cx4_validation_center.freeze import freeze_check
from gunnchos_device_os.cx4_validation_center.materiality import (
    MaterialityClass,
    apply_material_invalidation,
    compare_freeze,
)
from gunnchos_device_os.cx4_validation_center.rehearsal import run_rehearsal
from gunnchos_device_os.cx4_validation_center.store import StoreError, ValidationStore
from gunnchos_device_os.cx4_validation_center.export import export_json
from gunnchos_device_os.cx4_validation_center.gates import can_promote_gate, enforce_pending_tokens
from gunnchos_device_os.cx4_validation_center.tokens import Cx41Tokens

ROOT = Path(__file__).resolve().parents[2]


def _store(tmp_path: Path) -> ValidationStore:
    return ValidationStore(tmp_path / "store")


def test_default_eligibility_is_pilot(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="person-a",
        moderator="mod",
    )
    assert s["evidence_eligibility"] == ValidationEvidenceEligibility.PILOT_NON_GATING.value


def test_rehearsal_cannot_become_gating(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="rehearsal-bot",
        moderator="mod",
        is_rehearsal=True,
        evidence_eligibility=ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value,
    )
    with pytest.raises(StoreError) as ei:
        store.set_evidence_eligibility(
            s["session_id"],
            ValidationEvidenceEligibility.FINAL_GATING_ELIGIBLE.value,
            role="reviewer",
        )
    assert ei.value.code == "eligibility_forbidden"
    with pytest.raises(StoreError):
        store.set_evidence_eligibility(
            s["session_id"],
            ValidationEvidenceEligibility.PILOT_NON_GATING.value,
            role="moderator",
        )


def test_pilot_cannot_become_accepted_final(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="pilot-a",
        moderator="mod",
    )
    with pytest.raises(StoreError):
        store.set_evidence_eligibility(
            s["session_id"],
            ValidationEvidenceEligibility.FINAL_GATING_ACCEPTED.value,
            role="moderator",
        )
    with pytest.raises(StoreError):
        store.reviewer_signoff(
            s["session_id"],
            "vc_software_smoke_walkthrough",
            signoff=True,
            role="reviewer",
            accept_as_final_gating=True,
        )


def test_participant_cannot_alter_eligibility(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="p",
        moderator="mod",
    )
    with pytest.raises(StoreError) as ei:
        store.set_evidence_eligibility(
            s["session_id"],
            ValidationEvidenceEligibility.FINAL_GATING_ELIGIBLE.value,
            role="participant",
        )
    assert "participant" in ei.value.detail or ei.value.code == "eligibility_forbidden"


def test_reviewer_cannot_promote_material_drift_invalidated(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="p",
        moderator="mod",
    )
    sess = store.load_session(s["session_id"])
    sess["evidence_eligibility"] = ValidationEvidenceEligibility.INVALIDATED_BY_MATERIAL_DRIFT.value
    store.save_session(sess)
    with pytest.raises(StoreError):
        store.set_evidence_eligibility(
            s["session_id"],
            ValidationEvidenceEligibility.FINAL_GATING_ACCEPTED.value,
            role="reviewer",
        )


def test_freeze_check_fails_eligibility_when_draft(tmp_path):
    report = freeze_check(ROOT)
    assert report["CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS"] is True
    assert report["CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE"] is False
    assert report["FINAL_GATING_ELIGIBLE"] is False
    assert report["missing_conditions"]


def test_material_change_invalidates_affected_pack():
    prior = {
        "provenance": {"commit": "aaa", "branch": "old"},
        "manifest": {"pack_ids": ["human_a11y"]},
        "task_pack_hashes": {"human_a11y": "0" * 64, "physical_printer": "1" * 64},
        "ui_fingerprint": "old",
        "a11y_fingerprint": "old",
        "evidence_pipeline_fingerprint": "old",
        "task_logic_fingerprint": "old",
    }
    current = {
        "device_os_commit": "bbb",
        "branch": "new",
        "task_pack_hashes": {"human_a11y": "f" * 64, "physical_printer": "1" * 64},
        "ui_fingerprint": "new-ui",
        "a11y_fingerprint": "new-a11y",
        "evidence_pipeline_fingerprint": "old",
        "task_logic_fingerprint": "new-logic",
        "validation_task_schema_version": "v1",
    }
    result = compare_freeze(prior, current)
    assert result["is_material"] is True
    assert "human_a11y" in result["affected_packs"]
    session = apply_material_invalidation(
        {"evidence_eligibility": "FINAL_GATING_ELIGIBLE", "pack_ids": ["human_a11y"]},
        result,
    )
    assert session["evidence_eligibility"] == ValidationEvidenceEligibility.INVALIDATED_BY_MATERIAL_DRIFT.value


def test_session_code_enumeration_fails(tmp_path):
    store = _store(tmp_path)
    store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="p",
        moderator="mod",
    )
    with pytest.raises(StoreError) as ei:
        store.join_by_code("ZZ")
    assert ei.value.code in {"session_code_invalid", "session_join_denied"}
    with pytest.raises(StoreError) as ei2:
        store.join_by_code("NOTREAL1")
    assert ei2.value.code == "session_join_denied"


def test_revoked_session_denied(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="p",
        moderator="mod",
    )
    store.revoke_access(s["session_id"])
    with pytest.raises(StoreError) as ei:
        store.join_by_code(s["session_code"], access_token=s["access_token"])
    assert ei.value.code == "access_revoked"


def test_restore_preserves_ratings_evidence(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="p",
        moderator="mod",
    )
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True, "media_photo": False})
    store.patch_task_result(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        {
            "participant_rating": {
                "completion": "completed_successfully",
                "ease": 4,
                "confidence": 4,
                "satisfaction": 4,
                "accessibility_impact": "none",
            }
        },
    )
    store.add_evidence_bytes(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        file_name="n.txt",
        mime="text/plain",
        data=b"keep-me",
    )
    bak = store.backup_pending_sessions(tmp_path / "bak")
    store2 = ValidationStore(tmp_path / "store2")
    store2.restore_pending_sessions(Path(bak["dest"]))
    loaded = store2.load_session(s["session_id"])
    assert loaded["task_results"][0]["participant_rating"]["ease"] == 4
    assert loaded["evidence"][0]["file_name"] == "n.txt"
    assert loaded["evidence_eligibility"] == "PILOT_NON_GATING"


def test_exports_preserve_evidence_class(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="p",
        moderator="mod",
        evidence_eligibility="PILOT_NON_GATING",
    )
    text = export_json(store.load_session(s["session_id"]))
    assert "PILOT_NON_GATING" in text


def test_one_click_launcher_never_kills_foreign_processes():
    script = (ROOT / "scripts" / "start-validation-center").read_text(encoding="utf-8")
    assert "kill unrelated" not in script.lower() or "Never kills unrelated" in script or "never kill" in script.lower()
    assert "Refusing to kill" in script
    assert "cx4_validation_center" in script
    assert "--lan" in script
    assert "127.0.0.1" in script or "loopback" in script.lower()


def test_rehearsal_flow_pass(tmp_path):
    root = tmp_path / "reh"
    root.mkdir()
    (root / ".rehearsal_reset_allowed").write_text("ok\n", encoding="utf-8")
    report = run_rehearsal(root, repo_root=ROOT, reset=False)
    assert report["CX4_VALIDATION_REHEARSAL_FLOW_PASS"] is True
    assert report["evidence_eligibility"] == "REHEARSAL_NON_GATING"
    assert report["real_human_session"] is False
    assert report["gate_promotion_allowed"] is False


def test_pending_gates_remain():
    t = enforce_pending_tokens(Cx41Tokens())
    assert t.J6_CLASS == "HUMAN_VALIDATION_PENDING"
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert t.CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE is False
    assert t.PHYSICAL_PRINTER_PENDING and t.EVT_PENDING and t.DVT_PENDING and t.PVT_PENDING


def test_docs_packet_exists():
    docs = ROOT / "docs" / "complete-experience" / "cx4_validation_center"
    assert (docs / "HUMAN_VALIDATION_DAY_RUNBOOK.md").is_file()
    assert (docs / "QUICK_START_HUMAN_VALIDATION.md").is_file()
    assert (docs / "PARTICIPANT_GUIDE.md").is_file()


def test_ui_contains_pilot_surfaces():
    index = (ROOT / "apps" / "validation_center" / "index.html").read_text(encoding="utf-8")
    assert "Enter Session Code" in index
    assert "moderator-wizard" in index
    assert "Add Screenshot" in index
    assert "Awaiting Review" in index
    assert "I need help" in index or "need-help" in index
    assert "Prefer not to answer" in index or "prefer-not-to-answer" in index
