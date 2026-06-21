"""DS-XL deploy contract — package transport and safety model."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "deploy_targets.yaml"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def list_deploy_targets() -> list[str]:
    return list(_load().get("deploy_targets", {}).keys())


def get_deploy_target(target_id: str) -> dict[str, Any]:
    targets = _load().get("deploy_targets", {})
    if target_id not in targets:
        raise ValueError(f"Unknown deploy target: {target_id}")
    return {"id": target_id, **targets[target_id]}


def get_transport_policy(transport: str) -> dict[str, Any]:
    transports = _load().get("transport_methods", {})
    if transport not in transports:
        raise ValueError(f"Unknown transport: {transport}")
    return {"transport": transport, **transports[transport]}


def deploy_package(
    source: str,
    target_id: str,
    package_type: str,
    transport: str,
    *,
    user_consent: bool = False,
    guardian_approved: bool = False,
) -> dict[str, Any]:
    target = get_deploy_target(target_id)
    policy = get_transport_policy(transport)

    if package_type not in target.get("allowed_package_types", []):
        return _failure(
            f"'{package_type}' is not allowed on {target['display_name']}.",
            f"deploy_rejected:package_type={package_type} target={target_id}",
            "choose_allowed_package_type",
        )
    if transport not in target.get("allowed_transports", []):
        return _failure(
            f"'{transport}' is not supported for {target['display_name']}.",
            f"deploy_rejected:transport={transport} target={target_id}",
            "choose_allowed_transport",
        )
    safety = policy.get("safety_policy", {})
    if safety.get("requires_user_consent") and not user_consent:
        return _failure(
            "Deploy needs your OK first. Nothing was sent.",
            f"deploy_blocked:no_consent source={source} target={target_id}",
            "request_user_consent",
        )
    if target.get("guardian_restrictions") and not guardian_approved:
        return _failure(
            "A guardian or teacher must approve this deploy for this device.",
            f"deploy_blocked:guardian_required target={target_id}",
            "request_guardian_approval",
        )

    return {
        "success": True,
        "source": source,
        "target": target_id,
        "package_type": package_type,
        "transport": transport,
        "safety_policy_applied": safety,
        "rollback_path": "delete_package_or_rollback_placeholder",
        "user_message": f"Package ready on {target['display_name']}.",
        "technical_log": f"deploy_ok:source={source} target={target_id} pkg={package_type} via={transport}",
        "mock": True,
    }


def _failure(user_message: str, technical_log: str, next_action: str) -> dict[str, Any]:
    return {
        "success": False,
        "user_message": user_message,
        "technical_log": technical_log,
        "next_action": next_action,
        "safe_fallback": "local_folder_export",
        "mock": True,
    }
