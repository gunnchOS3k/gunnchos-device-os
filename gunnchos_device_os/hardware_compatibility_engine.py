"""Hardware compatibility engine — profile-based mode/preset/app-pack checks."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .hardware_manifest_loader import load_device_profile
from .hardware_profile import CompatibilityResult
from ._hardware_policy_common import policy_result
from . import hardware_input_policy as input_policy
from . import hardware_mode_policy as mode_policy
from . import hardware_accessibility_policy as a11y_policy
from . import hardware_network_policy as network_policy

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "config" / "hardware_compatibility_rules.yaml"

BLOCKED_COMBOS = {
    ("wearables_arena_set", "Developer"): "WSL workstation not supported on wearables/arena",
    ("wearables_arena_set", "Workshop"): "Full developer workshop not supported on wearables/arena",
    ("wearables_arena_set", "wsl_path"): "WSL not supported",
}


@lru_cache(maxsize=1)
def _rules() -> dict[str, Any]:
    return yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))


def evaluate_compatibility(
    device_id: str,
    *,
    persona: str = "",
    journey_preset: str = "",
    mode: str = "",
    app_pack: str = "",
    consent: bool = False,
    guardian_approved: bool = False,
    marshal_control: bool = False,
    accessibility_needs: list[str] | None = None,
    offline_first: bool = False,
) -> CompatibilityResult:
    profile = load_device_profile(device_id)
    warnings: list[str] = []
    blockers: list[str] = []
    fallbacks: list[str] = []
    evidence: list[str] = ["real_hardware_validation_required"]

    # Mode check
    mode_res = mode_policy.check_mode(device_id, mode)
    if mode_res["status"] == "fail":
        blockers.append(mode_res["message"])
        if mode_res.get("fallback"):
            fallbacks.append(mode_res["fallback"])
    elif mode_res["status"] == "warn":
        warnings.append(mode_res["message"])

    # Blocked combos
    key = (device_id, mode)
    if key in BLOCKED_COMBOS:
        blockers.append(BLOCKED_COMBOS[key])
        fallbacks.append("arcade" if device_id == "wearables_arena_set" else "school")

    if device_id == "wearables_arena_set" and mode == "Developer":
        blockers.append("Unrestricted developer mode not allowed on wearables/arena")
        fallbacks.append("marshal_controlled_arcade")

    if device_id == "wearables_arena_set" and journey_preset == "spaceship":
        blockers.append("Spaceship mode not allowed without marshal controls")
        fallbacks.append("arcade")

    if device_id == "wearables_arena_set" and mode in ("Play", "Arcade") and not marshal_control:
        warnings.append("Arena play should use marshal/admin controls in venue settings")

    # Journey preset
    if journey_preset and journey_preset not in profile.supported_journey_presets:
        warnings.append(f"Preset {journey_preset} not in default profile list — checking mode matrix")
        fallbacks.append(profile.supported_journey_presets[0] if profile.supported_journey_presets else "scooter")

    # App pack
    if app_pack and app_pack not in profile.supported_app_packs:
        rules = _rules().get("app_pack_overrides", {})
        if app_pack not in rules.get(device_id, []):
            warnings.append(f"App pack {app_pack} may need constraints on {device_id}")

    # Research measurement consent
    if mode in ("Research Measurement", "Laboratory") and not consent:
        blockers.append("Research measurement requires explicit consent")
        fallbacks.append("offline")
        evidence.append("edge_io_consent_flow_validation")

    # Guardian for child personas
    if persona in ("pre_k_learner", "early_reader") and mode in ("Developer", "Admin", "Workshop"):
        if not guardian_approved:
            blockers.append("Guardian approval required for restricted mode on child profile")
            fallbacks.append("guardian")

    # Input policy
    inp = input_policy.check_input(device_id, mode)
    if inp["status"] == "fail":
        blockers.append(inp["message"])

    if accessibility_needs:
        a11y = a11y_policy.check_accessibility(device_id, accessibility_needs)
        if a11y["status"] == "warn":
            warnings.append(a11y["message"])

    if offline_first:
        net = network_policy.check_network(device_id, offline_first=True)
        if net["status"] == "warn":
            warnings.append(net["message"])

    compatible = len(blockers) == 0
    status = "pass" if compatible and not warnings else ("warn" if compatible else "fail")

    user_msg = "This device supports your selection." if compatible else (
        f"Let's try a safer option: {fallbacks[0]}" if fallbacks else "This combination is not supported on this device."
    )

    return CompatibilityResult(
        compatible=compatible,
        status=status,
        warnings=warnings,
        blockers=blockers,
        recommended_fallbacks=fallbacks,
        hardware_assumptions=profile.hardware_repo_source_paths,
        evidence_required=evidence,
        user_message=user_msg,
        technical_log=f"hw_compat:device={device_id} mode={mode} preset={journey_preset} status={status}",
    )
