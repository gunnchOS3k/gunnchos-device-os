"""Loader/validator for machine-readable image realm definitions.

Realm files live under ``os_build/image_realms/*.yaml`` (schema documented
in ``os_build/image_realms/SCHEMA.md``). This module is the single source
of truth other WP-013 code (``os_image_builder``, ``ab_update``,
``factory_provisioning``) reads realm policy from.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REALM_SCHEMA = "gunnchos.image_realm.v1"

REALM_FILES: dict[str, str] = {
    "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": "device_lab_interactive_development_guest.yaml",
    "EVT_ENGINEERING_IMAGE": "evt_engineering_image.yaml",
    "FACTORY_PROVISIONING_IMAGE": "factory_provisioning_image.yaml",
    "RECOVERY_IMAGE": "recovery_image.yaml",
    "PRODUCTION_SHIPPING_IMAGE_DEFINITION": "production_shipping_image_definition.yaml",
}

# Short aliases accepted by the CLI (`gunnchctl os-image build evt`, etc.)
REALM_ALIASES: dict[str, str] = {
    "lab": "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST",
    "dev": "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST",
    "dev_lab": "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST",
    "evt": "EVT_ENGINEERING_IMAGE",
    "factory": "FACTORY_PROVISIONING_IMAGE",
    "recovery": "RECOVERY_IMAGE",
    "production": "PRODUCTION_SHIPPING_IMAGE_DEFINITION",
    "prod": "PRODUCTION_SHIPPING_IMAGE_DEFINITION",
}


def resolve_realm_id(name: str) -> str:
    key = (name or "").strip()
    if key.upper() in REALM_FILES:
        return key.upper()
    alias = REALM_ALIASES.get(key.lower())
    if alias:
        return alias
    raise KeyError(f"unknown_realm:{name}")


def realm_dir(repo_root: Path) -> Path:
    return repo_root / "os_build" / "image_realms"


def load_realm(repo_root: Path, name: str) -> dict[str, Any]:
    realm_id = resolve_realm_id(name)
    path = realm_dir(repo_root) / REALM_FILES[realm_id]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"realm_file_malformed:{path}")
    return data


def load_all_realms(repo_root: Path) -> dict[str, dict[str, Any]]:
    return {rid: load_realm(repo_root, rid) for rid in REALM_FILES}


def validate_realm(realm: dict[str, Any]) -> list[str]:
    """Return a list of validation failure codes (empty == valid)."""
    failures: list[str] = []
    if realm.get("schema") != REALM_SCHEMA:
        failures.append("bad_schema")
    realm_id = realm.get("realm_id")
    if realm_id not in REALM_FILES:
        failures.append("unknown_realm_id")

    for key in (
        "packages",
        "debug_access",
        "developer_mode",
        "logging",
        "telemetry",
        "update_channel",
        "trust_roots",
        "secrets_policy",
        "recovery_behavior",
        "factory_only_services",
        "production_restrictions",
        "claim_boundary",
        "status",
    ):
        if key not in realm:
            failures.append(f"missing_field:{key}")

    trust_roots = realm.get("trust_roots") or {}
    if trust_roots.get("production_private_keys_present") is not False:
        failures.append("production_private_keys_present_not_false")

    if realm_id == "PRODUCTION_SHIPPING_IMAGE_DEFINITION":
        if realm.get("status") != "NOT_RELEASED":
            failures.append("production_status_must_be_not_released")
        if trust_roots.get("key_source") == "production":
            failures.append("production_key_source_forbidden_in_repo")
        restr = realm.get("production_restrictions") or {}
        if restr.get("debug_access_allowed") is not False:
            failures.append("production_debug_access_must_be_false")
        if restr.get("allow_unsigned_updates") is not False:
            failures.append("production_allow_unsigned_updates_must_be_false")

    if realm_id == "RECOVERY_IMAGE":
        rb = realm.get("recovery_behavior") or {}
        if rb.get("recovery_partition_required") is not True:
            failures.append("recovery_partition_required_must_be_true")

    if realm_id == "FACTORY_PROVISIONING_IMAGE":
        if not realm.get("factory_only_services"):
            failures.append("factory_only_services_must_be_nonempty")

    if realm_id in ("DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST", "EVT_ENGINEERING_IMAGE"):
        dm = realm.get("developer_mode") or {}
        if dm.get("enabled") is not True:
            failures.append("developer_mode_must_be_enabled")

    return failures


def validate_all(repo_root: Path) -> dict[str, Any]:
    results: dict[str, Any] = {}
    ok = True
    for realm_id in REALM_FILES:
        try:
            realm = load_realm(repo_root, realm_id)
            failures = validate_realm(realm)
        except Exception as exc:  # pragma: no cover - defensive
            failures = [f"load_error:{exc}"]
        results[realm_id] = {"ok": not failures, "failures": failures}
        ok = ok and not failures
    return {
        "ok": ok,
        "schema": REALM_SCHEMA,
        "realms": results,
        "IMAGE_REALMS_DIGITALLY_COMPLETE": ok and len(results) == len(REALM_FILES),
    }
