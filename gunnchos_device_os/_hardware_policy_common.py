"""Shared policy result helper."""
from __future__ import annotations

from typing import Any


def policy_result(
    status: str,
    message: str,
    *,
    fallback: str = "",
    evidence_required: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "fallback": fallback,
        "evidence_required": evidence_required,
    }
