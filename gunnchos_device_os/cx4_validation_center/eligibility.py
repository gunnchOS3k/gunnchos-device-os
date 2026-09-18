"""ValidationEvidenceEligibility v1 — fail-closed session class doctrine."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ValidationEvidenceEligibility(str, Enum):
    REHEARSAL_NON_GATING = "REHEARSAL_NON_GATING"
    PILOT_NON_GATING = "PILOT_NON_GATING"
    FINAL_GATING_ELIGIBLE = "FINAL_GATING_ELIGIBLE"
    FINAL_GATING_ACCEPTED = "FINAL_GATING_ACCEPTED"
    INVALIDATED_BY_MATERIAL_DRIFT = "INVALIDATED_BY_MATERIAL_DRIFT"


DEFAULT_ELIGIBILITY = ValidationEvidenceEligibility.PILOT_NON_GATING

# Classes that may never be treated as final human/physical gating evidence.
NON_GATING: Set[str] = {
    ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value,
    ValidationEvidenceEligibility.PILOT_NON_GATING.value,
    ValidationEvidenceEligibility.INVALIDATED_BY_MATERIAL_DRIFT.value,
}

# Classes that can only be assigned by freeze/acceptance machinery — never UI override.
FINAL_CLASSES: Set[str] = {
    ValidationEvidenceEligibility.FINAL_GATING_ELIGIBLE.value,
    ValidationEvidenceEligibility.FINAL_GATING_ACCEPTED.value,
}

# Moderator / participant may set only these.
MODERATOR_SETTABLE: Set[str] = {
    ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value,
    ValidationEvidenceEligibility.PILOT_NON_GATING.value,
}


FINAL_ELIGIBLE_REQUIREMENTS = (
    "tested_build_commit_frozen",
    "exact_application_provenance_recorded",
    "final_target_branch_or_rc_known",
    "no_material_code_change_after_freeze",
    "required_hardware_provider_prerequisites_real",
    "participant_not_synthetic_fixture",
    "reviewer_is_real_human",
    "consent_requirements_satisfied",
    "cx_stack_accepted_merged_or_release_candidate",
)


def normalize_eligibility(value: Optional[str], *, default: str = DEFAULT_ELIGIBILITY.value) -> str:
    raw = (value or default).strip()
    try:
        return ValidationEvidenceEligibility(raw).value
    except ValueError as exc:
        raise ValueError(f"unknown_eligibility:{raw}") from exc


def is_gating_capable(eligibility: str) -> bool:
    return normalize_eligibility(eligibility) in FINAL_CLASSES


def is_rehearsal(eligibility: str) -> bool:
    return normalize_eligibility(eligibility) == ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value


def assert_role_cannot_set_eligibility(role: str, requested: Optional[str]) -> None:
    """Moderator/participant/reviewer cannot force FINAL_* classes."""
    if requested is None:
        return
    elig = normalize_eligibility(requested)
    if elig in FINAL_CLASSES:
        raise PermissionError(f"role_cannot_set_final_eligibility:{role}:{elig}")
    if role == "participant" and elig != DEFAULT_ELIGIBILITY.value:
        # Participant may not change class at all (store rejects any participant patch).
        raise PermissionError("participant_cannot_alter_eligibility")
    if role in {"moderator", "reviewer"} and elig not in MODERATOR_SETTABLE:
        raise PermissionError(f"role_cannot_set_eligibility:{role}:{elig}")


def assert_cannot_promote_to_accepted(current: str, requested: str, *, role: str) -> None:
    cur = normalize_eligibility(current)
    req = normalize_eligibility(requested)
    if cur in NON_GATING and req in FINAL_CLASSES:
        raise PermissionError(f"cannot_promote_non_gating_to_final:{role}:{cur}->{req}")
    if cur == ValidationEvidenceEligibility.INVALIDATED_BY_MATERIAL_DRIFT.value and req in FINAL_CLASSES:
        raise PermissionError(f"cannot_promote_material_drift_invalidated:{role}")
    if cur == ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value and req != cur:
        if req in FINAL_CLASSES or req == ValidationEvidenceEligibility.PILOT_NON_GATING.value:
            # Rehearsal may stay rehearsal only (or be invalidated); never become pilot/final gating.
            if req in FINAL_CLASSES:
                raise PermissionError("rehearsal_cannot_become_gating")


def assert_reviewer_cannot_accept_as_final(session: Dict[str, Any]) -> None:
    elig = normalize_eligibility(session.get("evidence_eligibility"))
    if elig in NON_GATING:
        raise PermissionError(f"reviewer_cannot_accept_non_gating_as_final:{elig}")


def final_gating_missing_conditions(
    *,
    freeze: Optional[Dict[str, Any]] = None,
    session: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Explain why FINAL_GATING_ELIGIBLE is false for the current CX draft stack."""
    missing: List[str] = []
    freeze = freeze or {}
    session = session or {}

    if not freeze.get("build_frozen"):
        missing.append("tested_build_commit_frozen")
    if not freeze.get("application_provenance"):
        missing.append("exact_application_provenance_recorded")
    # Accept either legacy key or HumanValidationFreezeManifest field.
    target = (
        freeze.get("target_release_or_rc")
        or freeze.get("target_release_or_main_commit")
        or ""
    )
    if not str(target).strip():
        missing.append("final_target_branch_or_rc_known")
    if freeze.get("material_drift_detected"):
        missing.append("no_material_code_change_after_freeze")
    if not freeze.get("hardware_prerequisites_real"):
        missing.append("required_hardware_provider_prerequisites_real")
    if freeze.get("cx_stack_draft_unmerged", True):
        missing.append("cx_stack_accepted_merged_or_release_candidate")

    alias = (session.get("participant_alias") or "").lower()
    if session and (
        session.get("is_fixture")
        or session.get("is_rehearsal")
        or alias in {"template", "fixture", "test-fixture", "software-qa", "rehearsal-bot"}
    ):
        missing.append("participant_not_synthetic_fixture")
    if session and not (session.get("consent_state") or {}).get("accepted"):
        missing.append("consent_requirements_satisfied")
    if session and not (session.get("reviewer") or "").strip():
        # Real human reviewer must be named for final eligibility (not bot).
        missing.append("reviewer_is_real_human")
    elif session and "bot" in (session.get("reviewer") or "").lower():
        missing.append("reviewer_is_real_human")

    # Deduplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for m in missing:
        if m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered


def resolve_create_eligibility(
    requested: Optional[str],
    *,
    is_rehearsal_session: bool = False,
    allow_final: bool = False,
) -> str:
    if is_rehearsal_session:
        return ValidationEvidenceEligibility.REHEARSAL_NON_GATING.value
    if requested is None:
        return DEFAULT_ELIGIBILITY.value
    elig = normalize_eligibility(requested)
    if elig in FINAL_CLASSES and not allow_final:
        raise PermissionError("final_eligibility_requires_freeze_acceptance")
    if elig not in MODERATOR_SETTABLE and not allow_final:
        raise PermissionError(f"eligibility_not_settable:{elig}")
    return elig


def cx4_final_human_validation_eligible(freeze: Optional[Dict[str, Any]] = None) -> bool:
    """Token CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE — false until accepted/frozen target exists."""
    return len(final_gating_missing_conditions(freeze=freeze or {"cx_stack_draft_unmerged": True})) == 0
