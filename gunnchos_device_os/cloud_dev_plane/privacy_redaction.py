"""Privacy redaction for telemetry and diagnostics on the DEV plane."""
from __future__ import annotations

import re
from typing import Any

from gunnchos_device_os.diagnostics_log import redact as base_redact

_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_BEARER = re.compile(r"(?i)(bearer\s+)[a-z0-9._\-]+")
_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "ssn",
    "email",
    "phone",
    "student_name",
    "full_name",
    "enrollment_token",
}


def redact_string(value: str) -> str:
    value = _EMAIL.sub("[REDACTED_EMAIL]", value)
    value = _BEARER.sub(r"\1[REDACTED_TOKEN]", value)
    return value


def redact_payload(value: Any, *, parent_key: str | None = None) -> Any:
    """Redact nested payloads for OTEL attributes and service responses."""
    if parent_key and parent_key.lower() in _SENSITIVE_KEYS:
        return "[REDACTED]"
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if str(k).lower() in _SENSITIVE_KEYS:
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_payload(v, parent_key=str(k))
        return out
    if isinstance(value, list):
        return [redact_payload(v, parent_key=parent_key) for v in value]
    if isinstance(value, str):
        return redact_string(value)
    return base_redact(value, parent_key=parent_key)
