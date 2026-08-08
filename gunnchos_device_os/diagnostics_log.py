"""Persistent structured diagnostics log with redaction and OTel hooks.

Replaces in-memory mock security event log for the diagnostics path.
OpenTelemetry is optional: hooks emit span/log callbacks without requiring
the opentelemetry SDK. If the SDK is installed, export helpers can attach.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable
import json
import threading
import time
import uuid


SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "authorization",
    "message_content",
    "private_payload",
    "keystroke",
    "location",
    "ssn",
    "email",
    "phone",
}

REDACTED = "[REDACTED]"


def redact(value: Any, *, parent_key: str | None = None) -> Any:
    if parent_key and parent_key.lower() in SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, dict):
        return {k: redact(v, parent_key=k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, parent_key=parent_key) for v in value]
    if isinstance(value, str) and parent_key and parent_key.lower() in SENSITIVE_KEYS:
        return REDACTED
    return value


@dataclass
class OTelHooks:
    """Minimal OpenTelemetry-compatible callback surface (no hard dependency)."""

    on_log: Callable[[dict[str, Any]], None] | None = None
    on_span_start: Callable[[str, dict[str, Any]], Any] | None = None
    on_span_end: Callable[[Any, dict[str, Any]], None] | None = None

    def emit_log(self, record: dict[str, Any]) -> None:
        if self.on_log:
            self.on_log(record)

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        if self.on_span_start:
            return self.on_span_start(name, attributes or {})
        return {"name": name, "attributes": attributes or {}, "stub_span": True}

    def end_span(self, span: Any, attributes: dict[str, Any] | None = None) -> None:
        if self.on_span_end:
            self.on_span_end(span, attributes or {})


def try_attach_opentelemetry(hooks: OTelHooks) -> dict[str, Any]:
    """Attach real OTel LoggerProvider/Tracer if packages are installed."""
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry._logs import get_logger  # type: ignore
    except Exception as exc:  # noqa: BLE001 — optional dependency
        return {
            "attached": False,
            "reason": "opentelemetry_not_installed",
            "detail": str(exc.__class__.__name__),
        }

    tracer = trace.get_tracer("gunnchos.diagnostics")
    logger = get_logger("gunnchos.diagnostics")

    def on_span_start(name: str, attributes: dict[str, Any]) -> Any:
        return tracer.start_as_current_span(name, attributes=attributes)

    def on_span_end(span: Any, attributes: dict[str, Any]) -> None:
        if hasattr(span, "set_attributes") and attributes:
            span.set_attributes(attributes)
        if hasattr(span, "end"):
            span.end()

    def on_log(record: dict[str, Any]) -> None:
        # Prefer structured attributes; fall back to no-op if API differs.
        try:
            logger.emit(body=record.get("message", record.get("event_type", "log")), attributes=record)
        except Exception:  # noqa: BLE001
            pass

    hooks.on_span_start = on_span_start
    hooks.on_span_end = on_span_end
    hooks.on_log = on_log
    return {"attached": True, "reason": "opentelemetry_sdk"}


@dataclass
class DiagnosticsLog:
    path: Path
    hooks: OTelHooks = field(default_factory=OTelHooks)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def log(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
        *,
        level: str = "info",
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        safe_details = redact(details or {})
        record = {
            "id": f"evt-{uuid.uuid4().hex[:12]}",
            "ts_ms": int(time.time() * 1000),
            "level": level,
            "event_type": event_type,
            "details": safe_details,
            "trace_id": trace_id or uuid.uuid4().hex,
            "mock": False,
            "persistent": True,
        }
        line = json.dumps(record, sort_keys=True, default=str)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        self.hooks.emit_log(record)
        return record

    def span(self, name: str, attributes: dict[str, Any] | None = None):
        return _SpanContext(self, name, attributes or {})

    def read(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            if not self.path.exists():
                return []
            lines = self.path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            if not line.strip():
                continue
            out.append(json.loads(line))
        return out

    def clear(self) -> None:
        with self._lock:
            self.path.write_text("", encoding="utf-8")


class _SpanContext:
    def __init__(self, log: DiagnosticsLog, name: str, attributes: dict[str, Any]) -> None:
        self.log = log
        self.name = name
        self.attributes = redact(attributes)
        self.span: Any = None
        self.started_ms = 0

    def __enter__(self) -> dict[str, Any]:
        self.started_ms = int(time.time() * 1000)
        self.span = self.log.hooks.start_span(self.name, self.attributes)
        self.log.log("span_start", {"span": self.name, **self.attributes}, level="debug")
        return {"name": self.name, "span": self.span}

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        ended = int(time.time() * 1000)
        attrs = {
            "span": self.name,
            "duration_ms": ended - self.started_ms,
            "error": None if exc is None else str(exc),
        }
        self.log.hooks.end_span(self.span, attrs)
        self.log.log("span_end", attrs, level="error" if exc else "debug")
        return False


# Back-compat facade used by older callers expecting module-level APIs.
_DEFAULT: DiagnosticsLog | None = None


def get_default_log(path: str | Path | None = None) -> DiagnosticsLog:
    global _DEFAULT
    if _DEFAULT is None:
        target = Path(path) if path else Path("results/diagnostics/events.jsonl")
        _DEFAULT = DiagnosticsLog(path=target)
    return _DEFAULT


def log_event(event_type: str, details: dict[str, Any]) -> dict[str, Any]:
    return get_default_log().log(event_type, details)


def get_events(limit: int = 50) -> list[dict[str, Any]]:
    return get_default_log().read(limit=limit)


def clear_events() -> None:
    get_default_log().clear()
