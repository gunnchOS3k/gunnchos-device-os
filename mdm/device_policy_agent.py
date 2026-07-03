#!/usr/bin/env python3
"""Local MDM policy agent prototype — loads static JSON policy files.

Not production MDM: no remote server, enrollment, or fleet management.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "mdm" / "policy_schema.yaml"
REQUIRED_FIELDS = (
    "policy_id",
    "policy_version",
    "deployment_mode",
    "allowed_apps",
    "blocked_apps",
    "update_channel",
    "telemetry_consent_level",
)
ALLOWED_MODES = {"Play", "School", "Library", "Guardian", "Work"}
ALLOWED_CHANNELS = {"stable", "beta", "dev", "frozen"}
ALLOWED_TELEMETRY = {"none", "diagnostics", "analytics", "full"}


@dataclass
class PolicyDecision:
    app_id: str
    allowed: bool
    reason: str


@dataclass
class DevicePolicy:
    raw: dict[str, Any]
    path: Path

    @property
    def deployment_mode(self) -> str:
        return str(self.raw["deployment_mode"])

    @property
    def blocked_apps(self) -> set[str]:
        return set(self.raw.get("blocked_apps", []))

    @property
    def allowed_apps(self) -> set[str]:
        return set(self.raw.get("allowed_apps", []))


def validate_policy_dict(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
    mode = data.get("deployment_mode")
    if mode not in ALLOWED_MODES:
        errors.append(f"invalid deployment_mode: {mode!r}")
    channel = data.get("update_channel")
    if channel not in ALLOWED_CHANNELS:
        errors.append(f"invalid update_channel: {channel!r}")
    telemetry = data.get("telemetry_consent_level")
    if telemetry not in ALLOWED_TELEMETRY:
        errors.append(f"invalid telemetry_consent_level: {telemetry!r}")
    for key in ("allowed_apps", "blocked_apps"):
        val = data.get(key)
        if val is not None and not isinstance(val, list):
            errors.append(f"{key} must be a list")
    return errors


def load_policy(path: Path) -> DevicePolicy:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Policy must be a JSON object")
    errors = validate_policy_dict(data)
    if errors:
        raise ValueError("; ".join(errors))
    return DevicePolicy(raw=data, path=path)


def evaluate_app(policy: DevicePolicy, app_id: str) -> PolicyDecision:
    if app_id in policy.blocked_apps:
        return PolicyDecision(app_id, False, f"blocked by policy {policy.raw['policy_id']}")
    if policy.allowed_apps and app_id not in policy.allowed_apps:
        return PolicyDecision(app_id, False, "not in allowed_apps list")
    return PolicyDecision(app_id, True, "allowed by local MDM policy prototype")


def apply_policy_summary(policy: DevicePolicy) -> dict[str, Any]:
    """Return a summary suitable for shell/launcher consumption (prototype)."""
    return {
        "policy_id": policy.raw["policy_id"],
        "deployment_mode": policy.deployment_mode,
        "blocked_apps": sorted(policy.blocked_apps),
        "allowed_apps": sorted(policy.allowed_apps),
        "update_channel": policy.raw["update_channel"],
        "telemetry_consent_level": policy.raw["telemetry_consent_level"],
        "school_mode": policy.raw.get("school_mode", {}),
        "library_mode": policy.raw.get("library_mode", {}),
        "guardian_mode": policy.raw.get("guardian_mode", {}),
        "media_restrictions": policy.raw.get("media_restrictions", {}),
        "game_restrictions": policy.raw.get("game_restrictions", {}),
        "claim": "local static policy prototype — not production MDM",
    }


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: device_policy_agent.py <policy.json> [app_id]", file=sys.stderr)
        return 2
    policy_path = Path(args[0])
    if not policy_path.is_absolute():
        policy_path = ROOT / policy_path
    policy = load_policy(policy_path)
    summary = apply_policy_summary(policy)
    print(json.dumps(summary, indent=2))
    if len(args) > 1:
        decision = evaluate_app(policy, args[1])
        print(json.dumps({"app_id": decision.app_id, "allowed": decision.allowed, "reason": decision.reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
