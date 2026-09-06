"""Allowlist-only continuity handoff payload policy."""
from __future__ import annotations

import json
import re
from typing import Any

# Explicit allowlist — unknown fields dropped; secret-shaped values rejected.
HANDOFF_ALLOWLIST = frozenset(
    {
        "app_id",
        "registry_id",
        "bundle_id",
        "sdk_app_id",
        "runtime_id",
        "route",
        "deep_link",
        "course_id",
        "section_id",
        "activity_id",
        "lesson_id",
        "pct",
        "progress_pct",
        "checkpoint_label",
        "shell_form_factor",
        "from_profile",
        "to_profile",
        "sync_cursor",
        "revision",
        "display_hint",
    }
)

_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*")
_PEM_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
_API_KEY_RE = re.compile(r"(?i)\b(?:sk|rk|api)[_-][A-Za-z0-9_\-]{8,}\b|\b[A-Za-z0-9]*api[_-]?key[A-Za-z0-9_\-]*\b")


def _value_looks_secret(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if _PEM_RE.search(value):
        return True
    if _JWT_RE.search(value):
        return True
    if _BEARER_RE.search(value):
        return True
    if "WAIKE_DEV_DB_KEY" in value.upper():
        return True
    if _API_KEY_RE.search(value):
        return True
    return False


def continuity_handoff_payload(
    *,
    open_app_state: dict[str, Any],
    lesson_progress: dict[str, Any] | None,
    shell_form_factor: str,
    from_profile: str,
) -> dict[str, Any]:
    """Filter handoff to allowlist; reject nested secret sabotage closed."""
    included: list[str] = []
    dropped: list[str] = []
    rejected_secrets: list[str] = []

    def _filter(obj: Any, path: str) -> Any:
        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for k, v in obj.items():
                key = str(k)
                child = f"{path}.{key}" if path else key
                leaf = key.split(".")[-1]
                if leaf not in HANDOFF_ALLOWLIST and path == "":
                    # top-level unknown
                    dropped.append(child)
                    continue
                if path != "" and leaf not in HANDOFF_ALLOWLIST:
                    dropped.append(child)
                    continue
                if _value_looks_secret(v):
                    rejected_secrets.append(child)
                    continue
                if isinstance(v, (dict, list)):
                    filtered = _filter(v, child)
                    if isinstance(filtered, dict) and rejected_secrets:
                        # secrets found deeper — keep scanning
                        out[key] = filtered
                    else:
                        out[key] = filtered
                else:
                    out[key] = v
                    included.append(child)
            return out
        if isinstance(obj, list):
            return [_filter(x, f"{path}[]") for x in obj]
        if _value_looks_secret(obj):
            rejected_secrets.append(path or "<string>")
            return None
        return obj

    raw = {
        "app_id": open_app_state.get("app_id"),
        "registry_id": open_app_state.get("registry_id"),
        "bundle_id": open_app_state.get("bundle_id"),
        "sdk_app_id": open_app_state.get("sdk_app_id"),
        "runtime_id": open_app_state.get("runtime_id"),
        "shell_form_factor": shell_form_factor,
        "from_profile": from_profile,
    }
    # Merge allowlisted lesson progress fields only
    for k, v in (lesson_progress or {}).items():
        raw[k] = v

    _SECRET_KEY_NAMES = frozenset(
        {
            "password",
            "passwords",
            "private_key",
            "session_token",
            "db_key",
            "api_key",
            "secret",
            "bearer",
            "authorization",
            "auth",
            "jwt",
            "token",
            "answer_key",
            "lti_private_key",
            "waike_dev_db_key",
        }
    )

    def _key_is_secret(name: str) -> bool:
        n = name.lower()
        if n in _SECRET_KEY_NAMES:
            return True
        return any(s in n for s in ("password", "private_key", "token", "secret", "api_key", "bearer"))

    # Detect unknown / secret before filter for fail-closed on secrets
    for k, v in (lesson_progress or {}).items():
        if _key_is_secret(str(k)):
            rejected_secrets.append(str(k))
        elif k not in HANDOFF_ALLOWLIST:
            dropped.append(k)
        if _value_looks_secret(v):
            rejected_secrets.append(str(k))
        if isinstance(v, dict):
            for nk, nv in v.items():
                child = f"{k}.{nk}"
                if _key_is_secret(str(nk)):
                    rejected_secrets.append(child)
                elif nk not in HANDOFF_ALLOWLIST:
                    dropped.append(child)
                if _value_looks_secret(nv):
                    rejected_secrets.append(child)

    if rejected_secrets:
        return {
            "ok": False,
            "contains_secrets": True,
            "reason": "CONTINUITY_SECRET_REJECTED",
            "rejected_fields": sorted(set(rejected_secrets)),
            # Receipt: field names only — never leak stripped values
            "included_fields": [],
            "dropped_fields": sorted(set(dropped)),
            "payload": None,
        }

    clean = _filter(raw, "")
    # Recompute included from clean payload keys
    included = sorted(_flatten_keys(clean))
    return {
        "ok": True,
        "contains_secrets": False,
        "reason": None,
        "included_fields": included,
        "dropped_fields": sorted(set(dropped)),
        "rejected_fields": [],
        "payload": clean,
    }


def _flatten_keys(obj: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (dict, list)):
                keys.extend(_flatten_keys(v, path))
            else:
                keys.append(path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            keys.extend(_flatten_keys(v, f"{prefix}[{i}]"))
    return keys
