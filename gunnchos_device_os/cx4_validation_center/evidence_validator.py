"""Fail-closed validators that refuse incomplete human-validation evidence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.gates import session_is_template_or_fixture
from gunnchos_device_os.cx4_validation_center.library import get_task


REQUIRED_RATING_FIELDS = ("completion", "ease", "confidence", "satisfaction", "accessibility_impact")
COMPLETE_STATES = {"completed", "skipped", "skipped_with_reason", "blocked"}


def validate_session_completeness(session: Dict[str, Any]) -> Dict[str, Any]:
    """Return structured pass/fail. Never invents PASS for human/physical gates."""
    errors: List[str] = []
    warnings: List[str] = []

    if not session.get("session_id"):
        errors.append("session_id_missing")
    if not (session.get("consent_state") or {}).get("accepted"):
        errors.append("consent_not_accepted")
    if session_is_template_or_fixture(session):
        warnings.append("template_or_fixture_not_final_evidence")

    task_ids = list(session.get("task_ids") or [])
    results = {tr.get("task_id"): tr for tr in (session.get("task_results") or [])}
    evidence = list(session.get("evidence") or [])

    for tid in task_ids:
        task = get_task(tid)
        tr = results.get(tid)
        if not tr:
            errors.append(f"task_result_missing:{tid}")
            continue
        if tr.get("state") not in COMPLETE_STATES:
            errors.append(f"task_incomplete:{tid}:{tr.get('state')}")
        rating = tr.get("participant_rating") or {}
        # Ratings required when task reached a completed-like state.
        if tr.get("state") in {"completed", "blocked"}:
            for field in REQUIRED_RATING_FIELDS:
                if rating.get(field) in (None, ""):
                    errors.append(f"rating_incomplete:{tid}:{field}")
        required_ev = list((task.required_evidence if task else None) or [])
        if required_ev:
            refs = set(tr.get("evidence_refs") or [])
            if not refs:
                errors.append(f"evidence_refs_missing:{tid}")
            else:
                matched = [e for e in evidence if e.get("evidence_id") in refs]
                if not matched:
                    errors.append(f"evidence_objects_missing:{tid}")
                elif task and task.requires_physical and all(e.get("mock") for e in matched):
                    errors.append(f"physical_task_mock_only:{tid}")
        if task and task.requires_physical and tr.get("state") == "completed":
            if not any((not e.get("mock")) and e.get("task_id") == tid for e in evidence):
                errors.append(f"physical_completed_without_real_evidence:{tid}")

    status = session.get("session_status") or session.get("status")
    incomplete_open = [
        i for i in (session.get("issues") or []) if i.get("status") == "open" and i.get("blocking")
    ]
    if incomplete_open and status == "submitted":
        errors.append("blocking_issues_open_on_submit")

    ok = len(errors) == 0
    return {
        "ok": ok,
        "refused": not ok,
        "errors": errors,
        "warnings": warnings,
        "session_id": session.get("session_id"),
        "evidence_eligibility": session.get("evidence_eligibility"),
        "note": "Incomplete evidence is refused. Human/physical gate PASS is never auto-asserted.",
    }


def validate_submission_bundle(
    session: Dict[str, Any],
    submission: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base = validate_session_completeness(session)
    errors = list(base["errors"])
    status = session.get("session_status") or session.get("status")
    if status not in {"submitted", "reviewed", "exported"}:
        errors.append(f"session_not_submitted:{status}")
    if submission is not None:
        if not submission.get("submission_id"):
            errors.append("submission_id_missing")
        if submission.get("session_id") and submission.get("session_id") != session.get("session_id"):
            errors.append("submission_session_mismatch")
    ok = len(errors) == 0
    return {
        **base,
        "ok": ok,
        "refused": not ok,
        "errors": errors,
        "HUMAN_VALIDATION_EVIDENCE_COMPLETE": ok and not session_is_template_or_fixture(session),
    }
