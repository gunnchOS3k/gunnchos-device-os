"""Evidence-based compatibility classifier."""
from __future__ import annotations

from enum import Enum
from typing import Any


class CompatClass(str, Enum):
    NATIVE = "NATIVE"
    VERIFIED = "VERIFIED"
    PLAYABLE = "PLAYABLE"
    LIMITED = "LIMITED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


def classify(evidence: dict[str, Any]) -> dict[str, Any]:
    """Classify from execution evidence — never invent PASS."""
    present = bool(evidence.get("binary_present"))
    ran = bool(evidence.get("executed"))
    exit_code = evidence.get("exit_code")
    skipped = bool(evidence.get("skipped"))
    errors = evidence.get("errors") or []
    partial = bool(evidence.get("partial"))
    unsupported = bool(evidence.get("unsupported"))

    if skipped or not present:
        klass = CompatClass.UNKNOWN
        reason = evidence.get("skip_reason") or "binary_absent"
    elif unsupported:
        klass = CompatClass.UNSUPPORTED
        reason = "explicitly_unsupported"
    elif ran and exit_code == 0 and not errors and not partial:
        # native first-party vs verified third-party
        if evidence.get("lane") == "GUNNCH_NATIVE":
            klass = CompatClass.NATIVE
        else:
            klass = CompatClass.VERIFIED
        reason = "executed_clean"
    elif ran and exit_code == 0 and partial:
        klass = CompatClass.PLAYABLE
        reason = "executed_with_limitations"
    elif ran and (exit_code not in (0, None) or errors):
        klass = CompatClass.LIMITED
        reason = "executed_with_errors"
    else:
        klass = CompatClass.UNKNOWN
        reason = "insufficient_evidence"

    return {
        "class": klass.value,
        "reason": reason,
        "evidence": {
            "binary_present": present,
            "executed": ran,
            "exit_code": exit_code,
            "skipped": skipped,
            "partial": partial,
        },
    }
