"""Security event log — redacted admin and security events.

Persists via diagnostics_log when a path is configured; otherwise keeps an
in-memory ring for unit tests while marking mock=False for real redaction logic.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.diagnostics_log import DiagnosticsLog, redact

_EVENTS: list[dict[str, Any]] = []
_PERSISTENT: DiagnosticsLog | None = None


def configure_persistent_log(path: str | Path) -> DiagnosticsLog:
    global _PERSISTENT
    _PERSISTENT = DiagnosticsLog(path=Path(path))
    return _PERSISTENT


def log_event(event_type: str, details: dict[str, Any]) -> dict[str, Any]:
    if _PERSISTENT is not None:
        entry = _PERSISTENT.log(event_type, details)
        _EVENTS.append(entry)
        return entry
    redacted = redact(details)
    entry = {
        "event_type": event_type,
        "details": redacted,
        "mock": False,
        "persistent": False,
    }
    _EVENTS.append(entry)
    return entry


def get_events(limit: int = 50) -> list[dict[str, Any]]:
    if _PERSISTENT is not None:
        return _PERSISTENT.read(limit=limit)
    return list(_EVENTS[-limit:])


def clear_events(*, reset_persistent: bool = False) -> None:
    global _PERSISTENT
    _EVENTS.clear()
    if _PERSISTENT is not None:
        _PERSISTENT.clear()
    if reset_persistent:
        _PERSISTENT = None
