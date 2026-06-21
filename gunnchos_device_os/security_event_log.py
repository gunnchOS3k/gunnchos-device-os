"""Security event log — redacted admin and security events."""
from __future__ import annotations

from typing import Any

_EVENTS: list[dict[str, Any]] = []
_SENSITIVE_KEYS = {"password", "message_content", "private_payload", "keystroke", "location"}


def log_event(event_type: str, details: dict[str, Any]) -> dict[str, Any]:
    redacted = {k: ("[REDACTED]" if k in _SENSITIVE_KEYS else v) for k, v in details.items()}
    entry = {
        "event_type": event_type,
        "details": redacted,
        "mock": True,
    }
    _EVENTS.append(entry)
    return entry


def get_events(limit: int = 50) -> list[dict[str, Any]]:
    return list(_EVENTS[-limit:])


def clear_events() -> None:
    _EVENTS.clear()
