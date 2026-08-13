"""Shared sandbox/runtime helpers for first-party gunnchSDK apps.

Digital dogfood only — not a shipping app framework or production sandbox.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


CLAIM_BOUNDARY = (
    "Digital first-party app runtime helpers for gunnchSDK dogfood. "
    "Not a production OS sandbox, not store distribution, not physical device proof."
)


def sandbox_data_dir() -> Path:
    raw = os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR")
    if raw:
        path = Path(raw)
    else:
        path = Path.cwd() / ".gunnchos_app_data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_id() -> str:
    return os.environ.get("GUNNCHOS_APP_ID", "gunnchos.unknown")


def app_version() -> str:
    return os.environ.get("GUNNCHOS_APP_VERSION", "0.0.0")


def network_policy() -> str:
    return os.environ.get("GUNNCHOS_SANDBOX_NETWORK_POLICY", "deny_all")


def assert_permissions(required: list[str], granted: list[str] | None = None) -> dict[str, Any]:
    """Digitally enforce declared permissions against an allow-list.

    When GUNNCHOS_APP_PERMISSIONS is set (comma-separated), it is the grant set.
    Otherwise ``granted`` (or required==granted fallback for local runs) is used.
    """
    env_raw = os.environ.get("GUNNCHOS_APP_PERMISSIONS")
    if env_raw is not None:
        grant = {p.strip() for p in env_raw.split(",") if p.strip()}
    elif granted is not None:
        grant = set(granted)
    else:
        grant = set(required)
    missing = [p for p in required if p not in grant]
    return {
        "ok": not missing,
        "required": list(required),
        "granted": sorted(grant),
        "missing": missing,
        "network_policy": network_policy(),
    }


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def append_app_log(event: str, detail: dict[str, Any] | None = None) -> str:
    data = sandbox_data_dir()
    log_path = data / "app_runtime.log"
    line = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "app_id": app_id(),
        "version": app_version(),
        "event": event,
        "detail": detail or {},
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
    return str(log_path)


def intentional_crash_probe(*, enabled: bool) -> None:
    """Optional crash path used by dogfood to prove crash_report generation."""
    if enabled:
        raise RuntimeError("platform001_intentional_crash_probe")
