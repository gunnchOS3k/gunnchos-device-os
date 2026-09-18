"""Automated REHEARSAL_NON_GATING session — never counts as real human evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx4_validation_center.contracts import EvidenceSource, _now
from gunnchos_device_os.cx4_validation_center.eligibility import ValidationEvidenceEligibility
from gunnchos_device_os.cx4_validation_center.export import (
    export_bundle_zip,
    export_csv,
    export_html,
    export_json,
)
from gunnchos_device_os.cx4_validation_center.gates import can_promote_gate
from gunnchos_device_os.cx4_validation_center.store import StoreError, ValidationStore


REHEARSAL_ALIAS = "rehearsal-bot"
REHEARSAL_RESET_MARKER = ".rehearsal_reset_allowed"


def run_rehearsal(
    root: Path,
    *,
    repo_root: Optional[Path] = None,
    reset: bool = False,
) -> Dict[str, Any]:
    """
    Prove create → join → rate → evidence → submit → review → export.
    Marked REHEARSAL_NON_GATING and impossible to promote to human PASS.
    """
    root = Path(root)
    store = ValidationStore(root / "store")
    if reset:
        marker = root / REHEARSAL_RESET_MARKER
        if not marker.is_file():
            raise StoreError("rehearsal_reset_requires_explicit_marker")
        # Explicit test reset: wipe rehearsal sessions only
        for p in list(store.sessions_dir.glob("*.json")):
            try:
                data = __import__("json").loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("evidence_eligibility") == ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value:
                p.unlink(missing_ok=True)
                sid = data.get("session_id")
                if sid:
                    (store.autosave_dir / f"{sid}.json").unlink(missing_ok=True)

    session = store.create_session(
        pack_ids=["validation_center_smoke"],
        task_ids=["vc_software_smoke_walkthrough"],
        participant_alias=REHEARSAL_ALIAS,
        moderator="cx42-rehearsal-mod",
        reviewer="cx42-rehearsal-reviewer-bot",
        device_sku="host",
        build_version="cx4.2-rehearsal",
        branch="eng/cx4-validation-center-pilot-readiness",
        evidence_eligibility=ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value,
        is_rehearsal=True,
        is_fixture=True,
    )
    assert session["evidence_eligibility"] == ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value

    # Participant cannot alter eligibility
    participant_elig_blocked = False
    try:
        store.set_evidence_eligibility(session["session_id"], ValidationEvidenceEligibility.FINAL_GATING_ELIGIBLE.value, role="participant")
    except (StoreError, PermissionError):
        participant_elig_blocked = True

    store.record_consent(
        session["session_id"],
        {
            "accepted": True,
            "purpose_acknowledged": True,
            "plain_language_shown": True,
            "media_photo": True,
            "media_audio": False,
            "media_video": False,
        },
    )
    tid = "vc_software_smoke_walkthrough"
    store.patch_task_result(
        session["session_id"],
        tid,
        {
            "state": "completed",
            "started_at": _now(),
            "completed_at": _now(),
            "participant_completion": "completed_successfully",
            "participant_rating": {
                "completion": "completed_successfully",
                "ease": 4,
                "confidence": 4,
                "satisfaction": 4,
                "accessibility_impact": "none",
                "prefer_not_to_answer": False,
                "comment": "rehearsal only",
                "what_was_confusing": "",
                "what_would_make_easier": "",
            },
            "step_completions": [True, True, True, True, True, True],
        },
        role="participant",
    )
    store.add_evidence_bytes(
        session["session_id"],
        tid,
        file_name="rehearsal_note.txt",
        mime="text/plain",
        data=b"REHEARSAL_NON_GATING fixture evidence",
        source=EvidenceSource.HUMAN_OBSERVED.value,
        privacy_classification="internal",
        attribution="participant",
        notes="fixture",
        mock=True,
    )
    sub = store.submit_session(session["session_id"])
    # Ensure eligibility preserved on submission
    loaded = store.load_session(session["session_id"])
    assert loaded["evidence_eligibility"] == ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value

    # Reviewer sees submission and signs test review — still cannot promote
    store.reviewer_signoff(session["session_id"], tid, signoff=True, notes="rehearsal review only", role="reviewer")
    promote_blocked = False
    try:
        store.set_evidence_eligibility(
            session["session_id"],
            ValidationEvidenceEligibility.FINAL_GATING_ACCEPTED.value,
            role="reviewer",
        )
    except (StoreError, PermissionError):
        promote_blocked = True

    gate = can_promote_gate(store.load_session(session["session_id"]), tid, "human_a11y_pass")
    assert gate["allowed"] is False

    dest = root / "exports" / session["session_id"]
    dest.mkdir(parents=True, exist_ok=True)
    session_data = store.load_session(session["session_id"])
    (dest / "report.json").write_text(export_json(session_data, sub), encoding="utf-8")
    (dest / "report.csv").write_text(export_csv(session_data), encoding="utf-8")
    (dest / "report.html").write_text(export_html(session_data, sub), encoding="utf-8")
    export_bundle_zip(store.root, session_data, sub, dest / "evidence_bundle.zip")

    export_preserves = "REHEARSAL_NON_GATING" in (dest / "report.json").read_text(encoding="utf-8")

    return {
        "CX4_VALIDATION_REHEARSAL_FLOW_PASS": True,
        "session_id": session["session_id"],
        "evidence_eligibility": session["evidence_eligibility"],
        "submission_hash": sub.get("submission_hash"),
        "participant_eligibility_change_blocked": participant_elig_blocked,
        "reviewer_promotion_blocked": promote_blocked,
        "gate_promotion_allowed": gate["allowed"],
        "export_preserves_eligibility": export_preserves,
        "export_dir": str(dest),
        "real_human_session": False,
        "note": "Rehearsal is synthetic; do not count as a real human validation session.",
    }
