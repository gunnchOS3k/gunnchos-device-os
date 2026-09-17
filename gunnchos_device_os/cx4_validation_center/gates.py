"""Fail-closed human/physical gate promotion rules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.library import get_task
from gunnchos_device_os.cx4_validation_center.tokens import Cx41Tokens


REAL_EVIDENCE_CLASSES = {"HUMAN_OBSERVED", "HUMAN_OBSERVED+SYSTEM_CAPTURED", "SYSTEM_CAPTURED+HUMAN_OBSERVED"}


def session_is_template_or_fixture(session: Dict[str, Any]) -> bool:
    alias = (session.get("participant_alias") or "").lower()
    if alias in {"template", "fixture", "test-fixture", "software-qa"}:
        return True
    if session.get("is_fixture") or session.get("is_template"):
        return True
    # mock-only evidence cannot satisfy physical gates
    evidence = session.get("evidence") or []
    if evidence and all(e.get("mock") for e in evidence):
        return True
    return False


def task_reviewer_signed(session: Dict[str, Any], task_id: str) -> bool:
    for tr in session.get("task_results") or []:
        if tr.get("task_id") == task_id:
            return bool(tr.get("reviewer_signoff"))
    return False


def required_evidence_present(session: Dict[str, Any], task_id: str) -> bool:
    task = get_task(task_id)
    if not task:
        return False
    refs = set()
    for tr in session.get("task_results") or []:
        if tr.get("task_id") == task_id:
            refs = set(tr.get("evidence_refs") or [])
            break
    if not refs:
        return False
    # require at least one non-mock evidence item for gate tasks
    for e in session.get("evidence") or []:
        if e.get("evidence_id") in refs and not e.get("mock"):
            return True
    return False


def can_promote_gate(session: Dict[str, Any], task_id: str, gate_name: str) -> Dict[str, Any]:
    """Never auto-promote. Returns structured denial/allow for later human process."""
    reasons: List[str] = []
    task = get_task(task_id)
    if session_is_template_or_fixture(session):
        reasons.append("template_or_fixture_not_real_evidence")
    if not task:
        reasons.append("unknown_task")
    else:
        if task.requires_human and not (session.get("consent_state") or {}).get("accepted"):
            reasons.append("consent_missing")
        if task.pass_rule and "software" in (task.pass_rule or "").lower() and "N/A" in (task.pass_rule or ""):
            reasons.append("software_only_task")
        if not task_reviewer_signed(session, task_id):
            reasons.append("reviewer_signoff_required")
        if not required_evidence_present(session, task_id):
            reasons.append("required_evidence_missing_or_mock_only")
        if task.requires_physical:
            # mocks never clear physical
            if any(e.get("mock") and e.get("task_id") == task_id for e in session.get("evidence") or []):
                if not any(
                    (not e.get("mock")) and e.get("task_id") == task_id for e in session.get("evidence") or []
                ):
                    reasons.append("physical_requires_non_mock_evidence")
    allowed = len(reasons) == 0
    return {
        "gate": gate_name,
        "task_id": task_id,
        "allowed": allowed,
        "reasons": reasons,
        "note": "Promotion is a separate human process; Validation Center never flips gates automatically.",
    }


def enforce_pending_tokens(tokens: Optional[Cx41Tokens] = None) -> Cx41Tokens:
    t = tokens or Cx41Tokens()
    t.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    t.PHYSICAL_PRINTER_PENDING = True
    t.PHYSICAL_CAMERA_MIC_AV_PENDING = True
    t.EVT_PENDING = True
    t.DVT_PENDING = True
    t.PVT_PENDING = True
    t.FULL_COMPLETE_EXPERIENCE_COMPLETE = False
    t.human_a11y_pass = False
    t.physical_printer_pass = False
    t.physical_camera_mic_av_pass = False
    t.evt_pass = False
    t.dvt_pass = False
    t.pvt_pass = False
    t.CX4_VALIDATION_REVIEWER_SIGNOFF_ENFORCED = True
    t.MINORS_MODE_DISABLED_BY_DEFAULT = True
    return t
