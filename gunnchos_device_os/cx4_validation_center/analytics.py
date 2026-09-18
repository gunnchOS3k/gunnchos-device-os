"""Descriptive session analytics — never auto-gates."""

from __future__ import annotations

from statistics import mean, median
from typing import Any, Dict, List, Optional


def _nums(values: List[Optional[float]]) -> List[float]:
    return [float(v) for v in values if v is not None and v != ""]


def summarize_session(session: Dict[str, Any]) -> Dict[str, Any]:
    results = session.get("task_results") or []
    total = len(results) or 1
    completed = sum(1 for tr in results if tr.get("state") == "completed")
    failed = sum(
        1
        for tr in results
        if (tr.get("participant_rating") or {}).get("completion") == "could_not_complete"
        or tr.get("participant_completion") == "could_not_complete"
    )
    ease = _nums([(tr.get("participant_rating") or {}).get("ease") for tr in results])
    conf = _nums([(tr.get("participant_rating") or {}).get("confidence") for tr in results])
    sat = _nums([(tr.get("participant_rating") or {}).get("satisfaction") for tr in results])
    issues = session.get("issues") or []
    sev_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for i in issues:
        try:
            sev_counts[int(i.get("severity"))] = sev_counts.get(int(i.get("severity")), 0) + 1
        except Exception:
            pass
    evidence = session.get("evidence") or []
    required_refs = set()
    for tr in results:
        required_refs.update(tr.get("evidence_refs") or [])
    return {
        "completion_rate": completed / total,
        "task_failure_count": failed,
        "ease_mean": mean(ease) if ease else None,
        "ease_median": median(ease) if ease else None,
        "confidence_mean": mean(conf) if conf else None,
        "satisfaction_mean": mean(sat) if sat else None,
        "issue_count": len(issues),
        "severity_counts": sev_counts,
        "evidence_completeness": (len(required_refs) / total) if total else 0,
        "evidence_item_count": len(evidence),
        "opaque_score": None,
        "note": "Descriptive only — does not promote gates.",
    }


def dashboard_buckets(sessions: List[Dict[str, Any]], packs: List[Dict[str, Any]]) -> Dict[str, Any]:
    ready = [p for p in packs if p.get("status") == "available"]
    pending_external = [p for p in packs if p.get("status") == "pending_external"]
    in_progress = [s for s in sessions if s.get("session_status") in {"in_progress", "paused", "consent_pending"}]
    submitted = [s for s in sessions if s.get("session_status") == "submitted"]
    needs = [s for s in sessions if s.get("session_status") in {"needs_clarification", "pending_submission"}]
    reviewed = [s for s in sessions if s.get("session_status") == "reviewed"]
    return {
        "ready_to_run": ready,
        "in_progress": in_progress,
        "submitted": submitted,
        "needs_attention": needs,
        "reviewed": reviewed,
        "pending_external": pending_external,
    }
