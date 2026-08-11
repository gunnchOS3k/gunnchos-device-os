"""Recovery / serviceability tooling: diagnostic bundle export,
backup/restore, device-replacement transfer, repair/service mode, user
data migration, log redaction, and secure wipe.

Operates on a plain "device root" directory (``user_data.json``,
``identity.json``, ``logs/*.log``) so tests run fully virtually against
tmp_path — no real device or disk partition involved.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import tarfile
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys

BACKUP_SCHEMA = "gunnchos.serviceability.backup.v1"
DIAGNOSTIC_SCHEMA = "gunnchos.serviceability.diagnostic_bundle.v1"

_REDACTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
    (re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[=:]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"\bDEVTEST-[A-Z0-9-]+\b"), "[REDACTED_SERIAL]"),
]


def redact_text(text: str) -> str:
    out = text
    for pattern, replacement in _REDACTION_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export_diagnostic_bundle(device_root: Path, out_path: Path) -> dict[str, Any]:
    """Real tar.gz containing redacted logs + a device-state summary."""
    device_root = Path(device_root)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logs_dir = device_root / "logs"
    redacted_entries: list[dict[str, Any]] = []
    staging = out_path.parent / f".{out_path.stem}_stage"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    stage_logs = staging / "logs"
    stage_logs.mkdir(parents=True, exist_ok=True)

    if logs_dir.exists():
        for log_file in sorted(logs_dir.glob("*.log")):
            raw = log_file.read_text(encoding="utf-8", errors="replace")
            redacted = redact_text(raw)
            dest = stage_logs / log_file.name
            dest.write_text(redacted, encoding="utf-8")
            redacted_entries.append({"name": log_file.name, "redacted": redacted != raw})

    identity_path = device_root / "identity.json"
    summary = {
        "schema": DIAGNOSTIC_SCHEMA,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity_present": identity_path.exists(),
        "log_files": redacted_entries,
        "claim_boundary": "Diagnostic bundle: logs are redacted before export; no raw secrets leave the device root.",
    }
    (staging / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if out_path.exists():
        out_path.unlink()
    with tarfile.open(out_path, "w:gz") as tar:
        for f in sorted(staging.rglob("*")):
            if f.is_file():
                tar.add(f, arcname=str(f.relative_to(staging)))
    shutil.rmtree(staging)

    return {
        "ok": True,
        "bundle_path": str(out_path),
        "sha256": _sha256_bytes(out_path.read_bytes()),
        "log_files_included": len(redacted_entries),
        "any_redaction_applied": any(e["redacted"] for e in redacted_entries),
    }


def backup_user_data(repo_root: Path, device_root: Path, backup_path: Path) -> dict[str, Any]:
    device_root = Path(device_root)
    backup_path = Path(backup_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    user_data_path = device_root / "user_data.json"
    identity_path = device_root / "identity.json"
    user_data = json.loads(user_data_path.read_text(encoding="utf-8")) if user_data_path.exists() else {}
    identity = json.loads(identity_path.read_text(encoding="utf-8")) if identity_path.exists() else {}

    backup = {
        "schema": BACKUP_SCHEMA,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity": identity,
        "user_data": user_data,
    }
    payload = json.dumps(backup, sort_keys=True).encode("utf-8")
    backup["signature_hex"] = dev_keys.sign_bytes(repo_root, payload)
    backup["signing_key_fingerprint"] = dev_keys.dev_public_key_fingerprint(repo_root)
    backup_path.write_text(json.dumps(backup, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "backup_path": str(backup_path), "sha256": _sha256_bytes(backup_path.read_bytes())}


def _verify_backup_signature(repo_root: Path, backup: dict[str, Any]) -> bool:
    core = {k: v for k, v in backup.items() if k not in ("signature_hex", "signing_key_fingerprint")}
    payload = json.dumps(core, sort_keys=True).encode("utf-8")
    return dev_keys.verify_bytes(repo_root, payload, backup.get("signature_hex", ""))


def restore_user_data(repo_root: Path, backup_path: Path, target_device_root: Path) -> dict[str, Any]:
    backup_path = Path(backup_path)
    target_device_root = Path(target_device_root)
    if not backup_path.exists():
        return {"ok": False, "error": "backup_not_found"}
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    if not _verify_backup_signature(repo_root, backup):
        return {"ok": False, "error": "backup_signature_invalid"}

    target_device_root.mkdir(parents=True, exist_ok=True)
    (target_device_root / "user_data.json").write_text(
        json.dumps(backup["user_data"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"ok": True, "restored_to": str(target_device_root), "backup_created_utc": backup["created_utc"]}


def transfer_device_replacement(
    repo_root: Path, old_device_root: Path, new_device_root: Path, *, transfer_reason: str
) -> dict[str, Any]:
    """Old-device -> new-device data transfer for hardware replacement.
    Backs up the old device, restores onto the new one, decommissions the
    old identity, and records a transfer receipt."""
    old_device_root = Path(old_device_root)
    new_device_root = Path(new_device_root)
    backup_path = old_device_root / ".transfer_backup.json"

    backup_result = backup_user_data(repo_root, old_device_root, backup_path)
    if not backup_result["ok"]:
        return backup_result
    restore_result = restore_user_data(repo_root, backup_path, new_device_root)
    if not restore_result["ok"]:
        return restore_result

    old_identity_path = old_device_root / "identity.json"
    if old_identity_path.exists():
        identity = json.loads(old_identity_path.read_text(encoding="utf-8"))
        identity["status"] = "DECOMMISSIONED_REPLACED"
        old_identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "gunnchos.serviceability.transfer_receipt.v1",
        "transfer_reason": transfer_reason,
        "old_device_root": str(old_device_root),
        "new_device_root": str(new_device_root),
        "ts": time.time(),
        "backup_sha256": backup_result["sha256"],
    }
    (new_device_root / "TRANSFER_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "receipt": receipt}


def enter_repair_mode(device_root: Path, *, reason: str) -> dict[str, Any]:
    device_root = Path(device_root)
    device_root.mkdir(parents=True, exist_ok=True)
    state_path = device_root / "SERVICE_MODE.json"
    state_path.write_text(
        json.dumps({"repair_mode": True, "reason": reason, "entered_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return {"ok": True, "repair_mode": True}


def exit_repair_mode(device_root: Path) -> dict[str, Any]:
    state_path = Path(device_root) / "SERVICE_MODE.json"
    if state_path.exists():
        state_path.unlink()
    return {"ok": True, "repair_mode": False}


def is_in_repair_mode(device_root: Path) -> bool:
    return (Path(device_root) / "SERVICE_MODE.json").exists()


USER_DATA_SCHEMA_V2 = "gunnchos.user_data.v2"


def migrate_user_data(user_data: dict[str, Any]) -> dict[str, Any]:
    """v1 (untagged, flat `accounts`/`settings`) -> v2 (schema-tagged,
    `settings.locale` guaranteed present, `apps` list guaranteed present)."""
    if user_data.get("schema") == USER_DATA_SCHEMA_V2:
        return dict(user_data)
    migrated = {
        "schema": USER_DATA_SCHEMA_V2,
        "accounts": list(user_data.get("accounts") or []),
        "apps": list(user_data.get("apps") or []),
        "settings": {"locale": "en-US", **(user_data.get("settings") or {})},
        "migrated_from_schema": user_data.get("schema", "gunnchos.user_data.v1_untagged"),
    }
    return migrated


def secure_wipe(device_root: Path, *, passes: int = 2) -> dict[str, Any]:
    """Overwrite every file's bytes with cryptographically random data
    (N passes) before deleting — models secure erase, not just unlink."""
    device_root = Path(device_root)
    if not device_root.exists():
        return {"ok": False, "error": "device_root_missing"}
    wiped_files = []
    for f in sorted(device_root.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            with f.open("wb") as fh:
                for _ in range(max(1, passes)):
                    fh.seek(0)
                    fh.write(secrets.token_bytes(size))
            wiped_files.append(str(f.relative_to(device_root)))
    shutil.rmtree(device_root)
    return {"ok": True, "wiped_files": wiped_files, "passes": passes, "device_root_removed": True}
