"""gunnchSDK app manifest schema (`gunnchos.sdk.app_manifest.v1`)."""
from __future__ import annotations

import re
from typing import Any

MANIFEST_SCHEMA = "gunnchos.sdk.app_manifest.v1"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")

VALID_PERMISSIONS = {
    "ring_input",
    "display_output",
    "network",
    "storage_read",
    "storage_write",
    "telemetry_read",
    "ai_interface",
    "camera",
    "microphone",
}

VALID_ARCH_TARGETS = {"aarch64", "x86_64", "wasm32"}

VALID_RUNTIMES = {"python", "godot"}

REQUIRED_FIELDS = (
    "schema",
    "app_id",
    "name",
    "version",
    "api_version",
    "min_os_version",
    "arch_targets",
    "entrypoint",
    "permissions",
    "capabilities_required",
    "sandbox_profile",
)


class ManifestError(ValueError):
    pass


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return a list of validation failure codes (empty == valid)."""
    failures: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in manifest:
            failures.append(f"missing_field:{field}")
    if failures:
        return failures

    if manifest.get("schema") != MANIFEST_SCHEMA:
        failures.append("bad_schema")

    app_id = manifest.get("app_id", "")
    if not re.match(r"^[a-z][a-z0-9_.\-]{2,63}$", app_id):
        failures.append("bad_app_id_format")

    for field in ("version", "api_version", "min_os_version"):
        val = manifest.get(field, "")
        if not SEMVER_RE.match(str(val)):
            failures.append(f"bad_semver:{field}")

    max_os = manifest.get("max_os_version")
    if max_os is not None and not SEMVER_RE.match(str(max_os)):
        failures.append("bad_semver:max_os_version")

    arch_targets = manifest.get("arch_targets") or []
    if not arch_targets or not set(arch_targets).issubset(VALID_ARCH_TARGETS):
        failures.append("bad_arch_targets")

    permissions = manifest.get("permissions") or []
    if not set(permissions).issubset(VALID_PERMISSIONS):
        failures.append("unknown_permission")

    caps = manifest.get("capabilities_required") or []
    if not isinstance(caps, list):
        failures.append("capabilities_required_must_be_list")

    sandbox = manifest.get("sandbox_profile") or {}
    if not isinstance(sandbox, dict) or "network_policy" not in sandbox:
        failures.append("sandbox_profile_missing_network_policy")

    deps = manifest.get("dependencies") or []
    for dep in deps:
        if not isinstance(dep, dict) or "app_id" not in dep or "min_version" not in dep:
            failures.append("bad_dependency_entry")
            break

    runtime = manifest.get("runtime", "python")
    if runtime not in VALID_RUNTIMES:
        failures.append("bad_runtime")
    if runtime == "godot":
        godot = manifest.get("godot") or {}
        if not isinstance(godot, dict) or not godot.get("main_pack"):
            failures.append("godot_main_pack_missing")

    return failures


def new_manifest(
    *,
    app_id: str,
    name: str,
    version: str = "0.1.0",
    api_version: str = "1.0.0",
    min_os_version: str = "0.3.0",
    max_os_version: str | None = None,
    arch_targets: list[str] | None = None,
    entrypoint: str = "main.py",
    permissions: list[str] | None = None,
    capabilities_required: list[str] | None = None,
    dependencies: list[dict[str, str]] | None = None,
    sandbox_network_policy: str = "deny_all",
    runtime: str = "python",
) -> dict[str, Any]:
    return {
        "schema": MANIFEST_SCHEMA,
        "app_id": app_id,
        "name": name,
        "version": version,
        "api_version": api_version,
        "min_os_version": min_os_version,
        "max_os_version": max_os_version,
        "arch_targets": arch_targets or ["aarch64", "x86_64"],
        "entrypoint": entrypoint,
        "runtime": runtime,
        "permissions": permissions or [],
        "capabilities_required": capabilities_required or [],
        "dependencies": dependencies or [],
        "sandbox_profile": {
            "network_policy": sandbox_network_policy,
            "filesystem_scope": f"/data/apps/{app_id}",
            "allow_ipc": False,
        },
    }
