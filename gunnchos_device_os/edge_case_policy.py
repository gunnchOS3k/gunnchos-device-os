"""Edge case policy — safe fallbacks for exceptional situations."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_edge_cases


def list_edge_cases() -> list[str]:
    return list(load_edge_cases().get("cases", {}).keys())


def _safe_format(template: str, context: dict[str, Any] | None) -> str:
    ctx = context or {}

    class _Safe(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return template.format_map(_Safe(ctx))


def handle_edge_case(case_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    cases = load_edge_cases().get("cases", {})
    if case_id not in cases:
        return {
            "case_id": case_id,
            "user_message": "Something unexpected happened. Let's try a safe default.",
            "safe_fallback": "scooter",
            "technical_log": f"unknown_edge_case:{case_id}",
            "next_action": "reset_to_safe_defaults",
        }
    case = cases[case_id]
    return {
        "case_id": case_id,
        "user_message": case["user_message"],
        "safe_fallback": case["safe_fallback"],
        "technical_log": _safe_format(case["technical_log"], context),
        "next_action": case["next_action"],
        "context": context or {},
    }
