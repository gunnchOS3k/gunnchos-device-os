"""Fail-closed CX4.1 Validation Center tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.cx4_validation_center.consent import MINORS_MODE_DISABLED_BY_DEFAULT, normalize_consent
from gunnchos_device_os.cx4_validation_center.contracts import EvidenceSource
from gunnchos_device_os.cx4_validation_center.edmund_map import map_edmund_to_tasks
from gunnchos_device_os.cx4_validation_center.export import export_json
from gunnchos_device_os.cx4_validation_center.gates import can_promote_gate, enforce_pending_tokens
from gunnchos_device_os.cx4_validation_center.library import build_task_library
from gunnchos_device_os.cx4_validation_center.security import security_self_check
from gunnchos_device_os.cx4_validation_center.a11y_audit import audit_validation_center_app
from gunnchos_device_os.cx4_validation_center.store import StoreError, ValidationStore
from gunnchos_device_os.cx4_validation_center.tokens import Cx41Tokens

ROOT = Path(__file__).resolve().parents[2]


def _store(tmp_path: Path) -> ValidationStore:
    return ValidationStore(tmp_path / "store")


def _smoke_session(store: ValidationStore, alias: str = "participant-a") -> dict:
    return store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias=alias,
        moderator="mod",
        device_sku="host",
    )


def test_template_not_human_evidence(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store, alias="template")
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    store.patch_task_result(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        {"state": "completed", "participant_rating": {"completion": "completed_successfully", "ease": 5, "confidence": 5, "satisfaction": 5, "accessibility_impact": "none"}},
    )
    store.add_evidence_bytes(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        file_name="note.txt",
        mime="text/plain",
        data=b"x",
        mock=True,
    )
    store.submit_session(s["session_id"])
    store.reviewer_signoff(s["session_id"], "vc_software_smoke_walkthrough", signoff=True, role="reviewer")
    decision = can_promote_gate(store.load_session(s["session_id"]), "vc_human_a11y_primary", "human_a11y_pass")
    assert decision["allowed"] is False


def test_fixture_not_physical_evidence(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["physical_printer"],
        task_ids=["vc_physical_printer"],
        participant_alias="fixture",
        moderator="mod",
    )
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True, "media_photo": True})
    store.add_evidence_bytes(
        s["session_id"],
        "vc_physical_printer",
        file_name="cups.json",
        mime="application/json",
        data=b"{}",
        source=EvidenceSource.SYSTEM_CAPTURED.value,
        mock=True,
    )
    decision = can_promote_gate(store.load_session(s["session_id"]), "vc_physical_printer", "physical_printer_pass")
    assert decision["allowed"] is False
    assert "template_or_fixture_not_real_evidence" in decision["reasons"] or "required_evidence_missing_or_mock_only" in decision["reasons"] or "reviewer_signoff_required" in decision["reasons"]


def test_participant_rating_not_reviewer_signoff(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    store.patch_task_result(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        {"state": "completed", "participant_rating": {"completion": "completed_successfully", "ease": 5, "confidence": 5, "satisfaction": 5, "accessibility_impact": "none"}},
    )
    loaded = store.load_session(s["session_id"])
    tr = loaded["task_results"][0]
    assert tr["participant_rating"]["completion"] == "completed_successfully"
    assert tr.get("reviewer_signoff") is False


def test_incomplete_session_cannot_submit_complete(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    with pytest.raises(StoreError) as ei:
        store.submit_session(s["session_id"])
    assert ei.value.code == "incomplete_session"


def test_submitted_snapshot_immutable(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    store.patch_task_result(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        {"state": "completed", "participant_rating": {"completion": "completed_successfully", "ease": 4, "confidence": 4, "satisfaction": 4, "accessibility_impact": "none"}},
    )
    store.add_evidence_bytes(s["session_id"], "vc_software_smoke_walkthrough", file_name="n.txt", mime="text/plain", data=b"ok")
    sub = store.submit_session(s["session_id"])
    with pytest.raises(StoreError) as ei:
        store.mutate_submission_in_place(s["session_id"], sub["version"], {"x": 1})
    assert ei.value.code == "submitted_snapshot_immutable"
    # amendment creates new version
    store2_path = tmp_path / "store"
    # unlock for amendment path: create new submission version by calling submit again after unlocking lock state
    store._submit_locks[s["session_id"]] = "done"
    # force incomplete false with completed tasks — second submit is amendment versioning
    # Need to allow re-submit as amendment: clear lock and call again
    sub2 = store.submit_session(s["session_id"])
    assert sub2["version"] == 2
    assert sub2["previous_submission_hash"] == sub["submission_hash"]
    assert sub2["submission_hash"] != sub["submission_hash"]


def test_declined_media_consent_blocks_media(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True, "media_photo": False})
    with pytest.raises(StoreError) as ei:
        store.add_evidence_bytes(
            s["session_id"],
            "vc_software_smoke_walkthrough",
            file_name="x.png",
            mime="image/png",
            data=b"\x89PNG",
        )
    assert ei.value.code == "media_consent_required"


def test_autosave_survives_restart(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    store.patch_task_result(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        {"participant_comments": "keep me"},
    )
    # simulate crash: delete primary session file, recover autosave
    path = store._session_path(s["session_id"])
    path.unlink()
    recovered = store.recover_from_autosave(s["session_id"])
    assert recovered["task_results"][0]["participant_comments"] == "keep me"


def test_duplicate_submit_prevented_while_pending(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    store.patch_task_result(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        {"state": "completed", "participant_rating": {"completion": "completed_successfully", "ease": 3, "confidence": 3, "satisfaction": 3, "accessibility_impact": "none"}},
    )
    store.add_evidence_bytes(s["session_id"], "vc_software_smoke_walkthrough", file_name="n.txt", mime="text/plain", data=b"ok")
    store._submit_locks[s["session_id"]] = "pending"
    with pytest.raises(StoreError) as ei:
        store.submit_session(s["session_id"])
    assert ei.value.code == "duplicate_submit_prevented"


def test_private_evidence_excluded_from_export(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    store.add_evidence_bytes(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        file_name="private.txt",
        mime="text/plain",
        data=b"secret",
        privacy_classification="private",
    )
    store.add_evidence_bytes(
        s["session_id"],
        "vc_software_smoke_walkthrough",
        file_name="public.txt",
        mime="text/plain",
        data=b"ok",
        privacy_classification="internal",
    )
    loaded = store.load_session(s["session_id"])
    exported = json.loads(export_json(loaded))
    names = [e["file_name"] for e in exported["evidence_manifest"]]
    assert "private.txt" not in names
    assert "public.txt" in names


def test_reviewer_signoff_required_and_not_forgeable(tmp_path):
    store = _store(tmp_path)
    s = _smoke_session(store)
    store.record_consent(s["session_id"], {"accepted": True, "purpose_acknowledged": True})
    with pytest.raises(PermissionError):
        store.patch_task_result(
            s["session_id"],
            "vc_software_smoke_walkthrough",
            {"reviewer_signoff": True},
            role="participant",
        )
    tokens = enforce_pending_tokens()
    assert tokens.CX4_VALIDATION_REVIEWER_SIGNOFF_ENFORCED is True


def test_gate_cannot_turn_true_without_evidence_class():
    t = enforce_pending_tokens(Cx41Tokens(CX4_VALIDATION_CENTER_GUI_PASS=True))
    assert t.human_a11y_pass is False
    assert t.J6_CLASS == "HUMAN_VALIDATION_PENDING"
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False


def test_minors_mode_disabled_by_default():
    assert MINORS_MODE_DISABLED_BY_DEFAULT is True
    c = normalize_consent({"accepted": True, "minors_mode": True})
    assert c["minors_mode"] is False


def test_task_library_not_all_active():
    tasks = build_task_library()
    assert len(tasks) >= 15
    assert any(t.active_by_default for t in tasks)
    assert not all(t.active_by_default for t in tasks)


def test_edmund_mapped():
    mapped = map_edmund_to_tasks(ROOT / "docs" / "complete-experience" / "cx4_readiness" / "CX4_EDMUND_ACTION_PACKET.md")
    assert mapped["packet_exists"] is True
    assert mapped["CX4_EDMUND_ACTION_PACKET_UI_MAPPED"] is True


def test_security_self_check():
    assert security_self_check()["ok"] is True


def test_a11y_audit_app():
    result = audit_validation_center_app(ROOT / "apps" / "validation_center")
    assert result["wcag_conformance_claimed"] is False
    assert result["CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS"] is True


def test_cx4_regression_tokens_still_pending():
    prior = ROOT / "artifacts" / "complete_experience" / "cx4_0" / "CX4_0_TOKENS.json"
    data = json.loads(prior.read_text())
    assert data["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert data["J6_CLASS"] == "HUMAN_VALIDATION_PENDING"
