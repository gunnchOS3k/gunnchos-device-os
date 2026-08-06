"""Boot manifest load/validate (production-shaped schema)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP = (
    "manifest_version",
    "image_id",
    "image_arch",
    "target_class",
    "services",
    "health_checks",
    "storage",
    "display",
    "network",
    "created_at",
)

SUPPORTED_TARGET_CLASSES = frozenset(
    {"host-native", "vm-container", "physical-candidate"}
)
SUPPORTED_ARCHES = frozenset({"x86_64", "amd64", "aarch64", "arm64", "armv7l", "host"})


class BootManifestError(ValueError):
    """Raised when a boot manifest is invalid or corrupted."""


def load_boot_manifest(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise BootManifestError(f"cannot read manifest: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BootManifestError(f"corrupted manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise BootManifestError("manifest root must be an object")
    validate_boot_manifest(data)
    return data


def validate_boot_manifest(data: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        raise BootManifestError(f"missing required fields: {', '.join(missing)}")

    target = data.get("target_class")
    if target not in SUPPORTED_TARGET_CLASSES:
        raise BootManifestError(
            f"unsupported target_class={target!r}; "
            f"expected one of {sorted(SUPPORTED_TARGET_CLASSES)}"
        )

    arch = str(data.get("image_arch", "")).lower()
    if arch not in SUPPORTED_ARCHES:
        raise BootManifestError(f"unsupported image_arch={arch!r}")

    services = data.get("services")
    if not isinstance(services, list) or not services:
        raise BootManifestError("services must be a non-empty list")
    for svc in services:
        if not isinstance(svc, dict) or "name" not in svc:
            raise BootManifestError("each service requires a name")

    health = data.get("health_checks")
    if not isinstance(health, list):
        raise BootManifestError("health_checks must be a list")

    storage = data.get("storage")
    if not isinstance(storage, dict) or "min_free_mb" not in storage:
        raise BootManifestError("storage.min_free_mb required")

    if "stale_after_days" in data and not isinstance(data["stale_after_days"], int):
        raise BootManifestError("stale_after_days must be int when present")
