"""API compatibility gate — stable capability IDs, semver rules, min OS
version, deprecation, and package rejection for incompatible manifests."""
from __future__ import annotations

from typing import Any

CURRENT_OS_VERSION = "0.3.0"
CURRENT_API_VERSION = "1.1.0"

# Stable capability IDs. Never remove/renumber an existing id — only add
# `deprecated_in` / `removed_in` fields, matching real platform practice.
CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = {
    "ring.read": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "ring.write": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "display.render": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "ai_interface.query": {"introduced_in": "0.2.0", "deprecated_in": None, "removed_in": None},
    "network.http": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "storage.read": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "storage.write": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "telemetry.read": {"introduced_in": "0.2.0", "deprecated_in": None, "removed_in": None},
    "identity.read": {"introduced_in": "0.1.0", "deprecated_in": None, "removed_in": None},
    "legacy.input_poll": {"introduced_in": "0.1.0", "deprecated_in": "0.2.0", "removed_in": "0.4.0"},
    "legacy.raw_socket": {"introduced_in": "0.1.0", "deprecated_in": "0.1.5", "removed_in": "0.3.0"},
}


def _parse_semver(value: str) -> tuple[int, int, int]:
    core = str(value).split("-", 1)[0]
    parts = core.split(".")
    while len(parts) < 3:
        parts.append("0")
    return tuple(int(p) for p in parts[:3])  # type: ignore[return-value]


def semver_lte(a: str, b: str) -> bool:
    return _parse_semver(a) <= _parse_semver(b)


def semver_lt(a: str, b: str) -> bool:
    return _parse_semver(a) < _parse_semver(b)


def semver_gte(a: str, b: str) -> bool:
    return _parse_semver(a) >= _parse_semver(b)


def check_capability(capability_id: str, os_version: str = CURRENT_OS_VERSION) -> dict[str, Any]:
    entry = CAPABILITY_REGISTRY.get(capability_id)
    if entry is None:
        return {"ok": False, "reason": "unknown_capability_id", "capability_id": capability_id}
    if not semver_gte(os_version, entry["introduced_in"]):
        return {"ok": False, "reason": "capability_not_yet_introduced", "capability_id": capability_id}
    if entry.get("removed_in") and semver_gte(os_version, entry["removed_in"]):
        return {"ok": False, "reason": "capability_removed", "capability_id": capability_id}
    deprecated = bool(entry.get("deprecated_in") and semver_gte(os_version, entry["deprecated_in"]))
    return {"ok": True, "deprecated": deprecated, "capability_id": capability_id}


def check_compatibility(
    manifest: dict[str, Any], *, os_version: str = CURRENT_OS_VERSION, api_version: str = CURRENT_API_VERSION
) -> dict[str, Any]:
    """Decide whether `os_version` running gunnchOS may install/run this
    package. This is the gate `gunnchctl install` calls before unpacking."""
    failures: list[str] = []
    warnings: list[str] = []

    min_os = manifest.get("min_os_version")
    max_os = manifest.get("max_os_version")
    if min_os and not semver_gte(os_version, min_os):
        failures.append(f"os_too_old:min_required={min_os},have={os_version}")
    if max_os and not semver_lte(os_version, max_os):
        failures.append(f"os_too_new:max_supported={max_os},have={os_version}")

    manifest_api = manifest.get("api_version")
    if manifest_api:
        if _parse_semver(manifest_api)[0] != _parse_semver(api_version)[0]:
            failures.append(f"api_major_version_mismatch:package={manifest_api},platform={api_version}")
        elif not semver_lte(manifest_api, api_version):
            failures.append(f"api_version_too_new:package={manifest_api},platform={api_version}")

    for cap_id in manifest.get("capabilities_required") or []:
        result = check_capability(cap_id, os_version=os_version)
        if not result["ok"]:
            failures.append(f"capability_incompatible:{cap_id}:{result['reason']}")
        elif result.get("deprecated"):
            warnings.append(f"capability_deprecated:{cap_id}")

    return {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "os_version": os_version,
        "platform_api_version": api_version,
        "API_COMPATIBILITY_GATE_EVALUATED": True,
    }
