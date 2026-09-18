"""Stream A: evidence refusal + refinement loop fail-closed tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.cx4_validation_center.evidence_validator import (
    validate_session_completeness,
    validate_submission_bundle,
)
from gunnchos_device_os.cx4_validation_center.freeze import freeze_check
from gunnchos_device_os.cx4_validation_center.refinement_loop import (
    intake_from_session,
    run_refinement_loop,
    triage_defect,
)
from gunnchos_device_os.cx4_validation_center.store import ValidationStore

ROOT = Path(__file__).resolve().parents[2]


def _store(tmp_path: Path) -> ValidationStore:
    return ValidationStore(tmp_path / "store")


def test_incomplete_session_refused(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="person-a",
        moderator="mod",
    )
    report = validate_session_completeness(store.load_session(s["session_id"]))
    assert report["refused"] is True
    assert any("consent" in e for e in report["errors"])


def test_complete_smoke_session_accepted_for_software_qa(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias="person-a",
        moderator="mod",
    )
    sid = s["session_id"]
    store.record_consent(sid, {"accepted": True, "purpose_acknowledged": True})
    store.patch_task_result(
        sid,
        "vc_software_smoke_walkthrough",
        {
            "state": "completed",
            "participant_rating": {
                "completion": "completed_successfully",
                "ease": 5,
                "confidence": 5,
                "satisfaction": 5,
                "accessibility_impact": "none",
            },
        },
    )
    store.add_evidence_bytes(
        sid,
        "vc_software_smoke_walkthrough",
        file_name="note.txt",
        mime="text/plain",
        data=b"walkthrough note",
        mock=False,
    )
    store.submit_session(sid)
    loaded = store.load_session(sid)
    report = validate_submission_bundle(loaded)
    assert report["ok"] is True
    assert report["HUMAN_VALIDATION_EVIDENCE_COMPLETE"] is True


def test_physical_mock_only_refused(tmp_path):
    store = _store(tmp_path)
    s = store.create_session(
        pack_ids=["physical_printer"],
        task_ids=["vc_physical_printer"],
        participant_alias="person-b",
        moderator="mod",
    )
    sid = s["session_id"]
    store.record_consent(sid, {"accepted": True, "purpose_acknowledged": True, "media_photo": True})
    store.patch_task_result(
        sid,
        "vc_physical_printer",
        {
            "state": "completed",
            "participant_rating": {
                "completion": "completed_successfully",
                "ease": 4,
                "confidence": 4,
                "satisfaction": 4,
                "accessibility_impact": "none",
            },
        },
    )
    store.add_evidence_bytes(
        sid,
        "vc_physical_printer",
        file_name="cups.json",
        mime="application/json",
        data=b"{}",
        mock=True,
    )
    report = validate_session_completeness(store.load_session(sid))
    assert report["refused"] is True
    assert any("physical" in e for e in report["errors"])


def test_refinement_loop_triages_digital_vs_human(tmp_path):
    session = {
        "session_id": "s1",
        "consent_state": {"accepted": True},
        "task_ids": ["vc_software_smoke_walkthrough"],
        "task_results": [
            {
                "task_id": "vc_software_smoke_walkthrough",
                "state": "completed",
                "participant_rating": {
                    "completion": "could_not_complete",
                    "ease": 1,
                    "confidence": 1,
                    "satisfaction": 1,
                    "accessibility_impact": "blocking_barrier",
                },
                "evidence_refs": [],
            }
        ],
        "issues": [
            {
                "issue_id": "i1",
                "task_id": "vc_software_smoke_walkthrough",
                "title": "Button unlabeled",
                "description": "UI label missing",
                "status": "open",
                "severity": "P1",
            }
        ],
        "evidence": [],
    }
    defects = [triage_defect(d) for d in intake_from_session(session)]
    assert defects
    assert any(d.track == "DIGITAL" for d in defects)
    report = run_refinement_loop([session], out_dir=tmp_path / "loop")
    assert report["HUMAN_REFINEMENT_LOOP_READY"] is True
    assert (tmp_path / "loop" / "REFINEMENT_LOOP_REPORT.json").is_file()


def test_freeze_check_recognizes_accepted_main_target():
    report = freeze_check(
        ROOT,
        portal_control_commit="6467551bbd68732d4681d763c35cc3b5da410879",
        target_release_or_main_commit="438aaf2b54d3365d681dd6eeeb73f6ac58663acc",
    )
    assert report["CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS"] is True
    manifest = report["manifest"]
    assert manifest["target_release_or_main_commit"]
    assert manifest["cx_stack_draft_unmerged"] is False
    # Hardware still pending → final gating remains false without owner attestation.
    assert "required_hardware_provider_prerequisites_real" in report["missing_conditions"]
    assert report["CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE"] is False
