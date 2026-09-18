"""Validation Center v1 contracts — versioned, local-first, fail-closed."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


CONTRACT_VERSION = "v1"


class EvidenceSource(str, Enum):
    SYSTEM_CAPTURED = "SYSTEM_CAPTURED"
    HUMAN_OBSERVED = "HUMAN_OBSERVED"


class SessionStatus(str, Enum):
    DRAFT = "draft"
    CONSENT_PENDING = "consent_pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    NEEDS_CLARIFICATION = "needs_clarification"
    REVIEWED = "reviewed"
    REVOKED = "revoked"


class ReviewerState(str, Enum):
    NOT_REVIEWED = "not_reviewed"
    IN_REVIEW = "in_review"
    EVIDENCE_SUFFICIENT = "evidence_sufficient"
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"
    CLARIFICATION_REQUESTED = "clarification_requested"
    SIGNED_OFF = "signed_off"


COMPLETION_OPTIONS = (
    "completed_successfully",
    "completed_with_difficulty",
    "could_not_complete",
    "not_attempted_skipped",
)

EASE_LABELS = {
    1: "Very difficult",
    2: "Difficult",
    3: "Neutral",
    4: "Easy",
    5: "Very easy",
}
CONFIDENCE_LABELS = {
    1: "Not confident",
    2: "Slightly confident",
    3: "Neutral",
    4: "Confident",
    5: "Very confident",
}
SATISFACTION_LABELS = {
    1: "Very dissatisfied",
    2: "Dissatisfied",
    3: "Neutral",
    4: "Satisfied",
    5: "Very satisfied",
}
A11Y_IMPACT_OPTIONS = (
    "none",
    "minor_friction",
    "moderate_barrier",
    "major_barrier",
    "blocking_barrier",
)
PHYSICAL_COMFORT_OPTIONS = (
    "comfortable",
    "slight_discomfort",
    "moderate_discomfort",
    "severe_discomfort",
    "stop_test",
)

DEFAULT_RATING_SCHEMA = {
    "completion": list(COMPLETION_OPTIONS),
    "ease": EASE_LABELS,
    "confidence": CONFIDENCE_LABELS,
    "satisfaction": SATISFACTION_LABELS,
    "accessibility_impact": list(A11Y_IMPACT_OPTIONS),
    "physical_comfort_optional": list(PHYSICAL_COMFORT_OPTIONS),
    "free_text": ["comment", "what_was_confusing", "what_would_make_easier"],
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def session_code() -> str:
    return secrets.token_urlsafe(6)[:8].upper()


def session_token() -> str:
    return secrets.token_urlsafe(32)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(blob)


def sanitize_filename(name: str) -> str:
    base = name.replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^\w.\-+=@ ]+", "_", base, flags=re.UNICODE).strip(" .")
    if not base or base in {".", ".."}:
        base = "attachment.bin"
    return base[:180]


@dataclass
class ValidationTask:
    task_id: str
    pack_id: str
    title: str
    short_description: str
    purpose: str
    evidence_class_target: str
    prerequisite_ids: List[str] = field(default_factory=list)
    estimated_minutes: int = 30
    safety_notes: List[str] = field(default_factory=list)
    participant_steps: List[str] = field(default_factory=list)
    moderator_steps: List[str] = field(default_factory=list)
    expected_result: str = ""
    pass_rule: str = ""
    required_evidence: List[str] = field(default_factory=list)
    optional_evidence: List[str] = field(default_factory=list)
    rating_schema: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_RATING_SCHEMA))
    issue_categories: List[str] = field(default_factory=list)
    device_or_sku: str = "any"
    requires_human: bool = True
    requires_physical: bool = False
    requires_external_provider: bool = False
    status: str = "available"  # available | inactive | pending_external
    version: str = CONTRACT_VERSION
    edmund_action_id: Optional[str] = None
    gate_unlocked: Optional[str] = None
    required_equipment: List[str] = field(default_factory=list)
    active_by_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationIssue:
    issue_id: str
    task_id: str
    severity: int
    category: str
    description: str
    reproduction: str = ""
    expected: str = ""
    observed: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    status: str = "open"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceItem:
    evidence_id: str
    file_name: str
    mime: str
    sha256: str
    timestamp: str
    source: str  # SYSTEM_CAPTURED | HUMAN_OBSERVED
    task_id: str
    privacy_classification: str  # public | internal | private | redacted
    attribution: str  # participant | moderator | system
    relative_path: str = ""
    notes: str = ""
    mock: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParticipantRating:
    completion: str = ""
    ease: Optional[int] = None
    confidence: Optional[int] = None
    satisfaction: Optional[int] = None
    accessibility_impact: str = ""
    physical_comfort: Optional[str] = None
    comment: str = ""
    what_was_confusing: str = ""
    what_would_make_easier: str = ""
    prefer_not_to_answer: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationTaskResult:
    task_id: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    participant_completion: str = ""
    participant_rating: Dict[str, Any] = field(default_factory=dict)
    participant_comments: str = ""
    moderator_observation: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    issue_refs: List[str] = field(default_factory=list)
    skip_reason: str = ""
    reviewer_state: str = ReviewerState.NOT_REVIEWED.value
    reviewer_notes: str = ""
    reviewer_signoff: bool = False
    step_completions: List[bool] = field(default_factory=list)
    paused: bool = False
    state: str = "not_started"  # not_started|in_progress|paused|completed|skipped

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsentState:
    accepted: bool = False
    declined: bool = False
    purpose_acknowledged: bool = False
    media_photo: bool = False
    media_audio: bool = False
    media_video: bool = False
    recorded_at: Optional[str] = None
    minors_mode: bool = False
    plain_language_shown: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PrivacyState:
    store_local_only: bool = True
    cloud_upload_enabled: bool = False
    export_excludes_private: bool = True
    redaction_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationSession:
    session_id: str
    pack_ids: List[str]
    participant_alias: str
    moderator: str
    reviewer: str = ""
    device_sku: str = ""
    build_version: str = ""
    branch: str = ""
    commit: str = ""
    started_at: Optional[str] = None
    submitted_at: Optional[str] = None
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    consent_state: Dict[str, Any] = field(default_factory=lambda: ConsentState().to_dict())
    privacy_state: Dict[str, Any] = field(default_factory=lambda: PrivacyState().to_dict())
    session_status: str = SessionStatus.DRAFT.value
    session_code: str = ""
    access_token: str = ""
    access_revoked: bool = False
    task_ids: List[str] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    final_comments: str = ""
    version: str = CONTRACT_VERSION
    lan_bind_opt_in: bool = False
    updated_at: Optional[str] = None
    evidence_eligibility: str = "PILOT_NON_GATING"
    is_rehearsal: bool = False
    is_fixture: bool = False
    expected_duration_minutes: int = 0
    session_title: str = ""
    privacy_summary: str = (
        "Your responses stay on this local Validation Center unless an operator exports them. "
        "You can stop at any time."
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationSubmission:
    submission_id: str
    session_id: str
    version: int
    manifest: Dict[str, Any]
    task_results: List[Dict[str, Any]]
    evidence_hashes: Dict[str, str]
    issue_list: List[Dict[str, Any]]
    provenance: Dict[str, Any]
    consent_state: Dict[str, Any]
    submission_timestamp: str
    submission_hash: str
    previous_submission_hash: Optional[str] = None
    contract_version: str = CONTRACT_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_rating(rating: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    completion = rating.get("completion") or ""
    if completion and completion not in COMPLETION_OPTIONS:
        errors.append("invalid_completion")
    for key, labels in (("ease", EASE_LABELS), ("confidence", CONFIDENCE_LABELS), ("satisfaction", SATISFACTION_LABELS)):
        val = rating.get(key)
        if val is not None and val != "" and int(val) not in labels:
            errors.append(f"invalid_{key}")
    impact = rating.get("accessibility_impact") or ""
    if impact and impact not in A11Y_IMPACT_OPTIONS:
        errors.append("invalid_accessibility_impact")
    comfort = rating.get("physical_comfort")
    if comfort and comfort not in PHYSICAL_COMFORT_OPTIONS:
        errors.append("invalid_physical_comfort")
    return errors
