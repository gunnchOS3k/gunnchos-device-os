"""Human refinement loop: defect intake → triage → digital fix track → revalidation.

Never auto-claims human/physical PASS. Digital-only defects may be marked
DIGITAL_FIX_READY; human/physical defects stay HUMAN_VALIDATION_REQUIRED or
PHYSICAL_HARDWARE_REQUIRED.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.contracts import _now, new_id
from gunnchos_device_os.cx4_validation_center.evidence_validator import validate_session_completeness
from gunnchos_device_os.cx4_validation_center.gates import can_promote_gate
from gunnchos_device_os.cx4_validation_center.library import get_task


ALLOWED_BLOCKER_CLASSES = (
    "HUMAN_VALIDATION_REQUIRED",
    "PHYSICAL_HARDWARE_REQUIRED",
    "EXTERNAL_PARTY_REQUIRED",
    "VENDOR_RESTRICTED_COLLATERAL_REQUIRED",
    "LEGAL_RIGHTS_REVIEW_REQUIRED",
    "PURCHASE_OR_FAB_AUTHORIZATION_REQUIRED",
)

SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass
class RefinementDefect:
    defect_id: str
    source_session_id: str
    task_id: str
    title: str
    description: str
    severity: str = "P2"
    track: str = "DIGITAL"  # DIGITAL | HUMAN | PHYSICAL | EXTERNAL | LEGAL
    blocker_class: Optional[str] = None
    status: str = "open"  # open | triaged | digital_fix_ready | awaiting_human | closed_wontfix
    evidence_refs: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    revalidation_required: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _infer_track(task_id: str, description: str = "") -> Dict[str, str]:
    task = get_task(task_id)
    blob = f"{task_id} {description}".lower()
    if task and task.requires_physical:
        return {"track": "PHYSICAL", "blocker_class": "PHYSICAL_HARDWARE_REQUIRED"}
    if "legal" in blob or "rights" in blob or "privacy review" in blob:
        return {"track": "LEGAL", "blocker_class": "LEGAL_RIGHTS_REVIEW_REQUIRED"}
    if "external" in blob or "issuer" in blob or "provider" in blob:
        return {"track": "EXTERNAL", "blocker_class": "EXTERNAL_PARTY_REQUIRED"}
    # Software-qualification / UI-only tasks are digital-fixable even if a human runs them.
    pass_rule = ((task.pass_rule if task else "") or "").lower()
    pack = (task.pack_id if task else "") or ""
    if (
        pack == "validation_center_smoke"
        or ("software" in pass_rule and "n/a" in pass_rule)
        or "ui" in blob
        or "label" in blob
        or "button" in blob
    ):
        return {"track": "DIGITAL", "blocker_class": None}
    if task and task.requires_human:
        return {"track": "HUMAN", "blocker_class": "HUMAN_VALIDATION_REQUIRED"}
    return {"track": "DIGITAL", "blocker_class": None}


def intake_from_session(session: Dict[str, Any]) -> List[RefinementDefect]:
    """Extract open/blocking issues + insufficient ratings into refinement defects."""
    defects: List[RefinementDefect] = []
    now = _now()
    for issue in session.get("issues") or []:
        if issue.get("status") not in {None, "open", "blocking", "needs_fix"}:
            continue
        tid = issue.get("task_id") or ""
        inferred = _infer_track(tid, issue.get("description") or issue.get("title") or "")
        defects.append(
            RefinementDefect(
                defect_id=issue.get("issue_id") or new_id("def"),
                source_session_id=session.get("session_id") or "",
                task_id=tid,
                title=issue.get("title") or f"Issue on {tid or 'session'}",
                description=issue.get("description") or "",
                severity=issue.get("severity") or "P2",
                track=inferred["track"],
                blocker_class=inferred["blocker_class"],
                status="open",
                evidence_refs=list(issue.get("evidence_refs") or []),
                created_at=now,
                updated_at=now,
            )
        )
    for tr in session.get("task_results") or []:
        rating = tr.get("participant_rating") or {}
        completion = rating.get("completion") or tr.get("participant_completion")
        a11y = rating.get("accessibility_impact")
        if completion in {"could_not_complete", "completed_with_difficulty"} or a11y in {
            "major_barrier",
            "blocking_barrier",
        }:
            tid = tr.get("task_id") or ""
            inferred = _infer_track(tid, completion or "")
            defects.append(
                RefinementDefect(
                    defect_id=new_id("def"),
                    source_session_id=session.get("session_id") or "",
                    task_id=tid,
                    title=f"Participant friction on {tid}",
                    description=f"completion={completion}; a11y={a11y}",
                    severity="P1" if a11y == "blocking_barrier" or completion == "could_not_complete" else "P2",
                    track=inferred["track"],
                    blocker_class=inferred["blocker_class"],
                    status="open",
                    evidence_refs=list(tr.get("evidence_refs") or []),
                    created_at=now,
                    updated_at=now,
                )
            )
    return defects


def triage_defect(defect: RefinementDefect) -> RefinementDefect:
    """Assign track/status. Digital defects become digital_fix_ready; others await authentic work."""
    d = RefinementDefect(**defect.to_dict())
    d.updated_at = _now()
    if d.severity not in SEVERITY_RANK:
        d.severity = "P2"
    if d.track == "DIGITAL":
        d.status = "digital_fix_ready"
        d.blocker_class = None
    else:
        d.status = "awaiting_human" if d.track == "HUMAN" else "triaged"
        if d.blocker_class not in ALLOWED_BLOCKER_CLASSES:
            inferred = _infer_track(d.task_id, d.description)
            d.blocker_class = inferred["blocker_class"] or "HUMAN_VALIDATION_REQUIRED"
    return d


def plan_revalidation(defect: RefinementDefect) -> Dict[str, Any]:
    """Describe how to re-earn after a fix. Never claims gate PASS."""
    task = get_task(defect.task_id)
    digital = defect.track == "DIGITAL"
    return {
        "defect_id": defect.defect_id,
        "task_id": defect.task_id,
        "revalidation_mode": "automated_digital_harness" if digital else "human_or_physical_session",
        "commands": (
            [
                "PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center qualify-pilot",
                "PYTHONPATH=.:src pytest -q tests/cx4_validation_center/",
            ]
            if digital
            else [
                "./scripts/start-validation-center",
                "PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center validate-session <session.json>",
            ]
        ),
        "gate_promotion_allowed_by_software": False,
        "gate_unlocked_if_human_passes": (task.gate_unlocked if task else None),
        "blocker_class": defect.blocker_class,
        "note": "Software may only clear DIGITAL track items. Human/physical gates remain pending until real evidence.",
    }


def run_refinement_loop(
    sessions: List[Dict[str, Any]],
    *,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Full digital refinement pipeline over Validation Center sessions."""
    defects: List[RefinementDefect] = []
    completeness: List[Dict[str, Any]] = []
    for session in sessions:
        completeness.append(validate_session_completeness(session))
        defects.extend(intake_from_session(session))

    triaged = [triage_defect(d) for d in defects]
    plans = [plan_revalidation(d) for d in triaged]

    digital_ready = [d for d in triaged if d.status == "digital_fix_ready"]
    awaiting = [d for d in triaged if d.status in {"awaiting_human", "triaged", "open"}]
    refused = [c for c in completeness if c.get("refused")]

    # Attempt gate promotion probes — must remain denied for fixtures/incomplete.
    promotion_probes = []
    for session in sessions:
        for tid in session.get("task_ids") or []:
            task = get_task(tid)
            gate = (task.gate_unlocked if task else None) or "unspecified"
            promotion_probes.append(can_promote_gate(session, tid, str(gate)))

    report = {
        "schema": "HUMAN_REFINEMENT_LOOP/v1",
        "generated_at": _now(),
        "sessions_processed": len(sessions),
        "defects": [d.to_dict() for d in triaged],
        "revalidation_plans": plans,
        "completeness": completeness,
        "promotion_probes": promotion_probes,
        "counts": {
            "defects_total": len(triaged),
            "digital_fix_ready": len(digital_ready),
            "awaiting_authentic_blocker": len(awaiting),
            "incomplete_sessions_refused": len(refused),
        },
        "HUMAN_REFINEMENT_LOOP_READY": True,
        "note": (
            "Refinement loop automation is ready. "
            "It refuses incomplete evidence and never auto-promotes human/physical gates."
        ),
    }

    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "REFINEMENT_LOOP_REPORT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        register = {
            "schema": "DEFECT_REGISTER/v1",
            "generated_at": _now(),
            "defects": report["defects"],
        }
        (out / "DEFECT_REGISTER.json").write_text(
            json.dumps(register, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        digest = hashlib.sha256(
            json.dumps(report["defects"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        (out / "DEFECT_REGISTER.sha256").write_text(digest + "\n", encoding="utf-8")

    return report
