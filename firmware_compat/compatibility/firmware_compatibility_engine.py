"""Firmware compatibility engine — manifest, profile, probe, and contract evaluation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from gunnchos_device_os.hardware_manifest_loader import load_device_profile

from .boot_readiness_checker import check_boot_readiness
from .capsule_update_client import stage_capsule
from .descriptor_matcher import match_descriptors
from .interface_contract_checker import check_interfaces

ROOT = Path(__file__).resolve().parents[2]
IMPORTED = ROOT / "firmware_compat" / "imported_hardware_contracts" / "manifests"


def load_firmware_manifest(device_id: str) -> dict[str, Any]:
    path = IMPORTED / f"{device_id}_firmware_manifest.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    hw_path = (
        ROOT.parent
        / "gunnchos-hardware-industrial-design"
        / "firmware"
        / "manifests"
        / f"{device_id}_firmware_manifest.yaml"
    )
    if hw_path.exists():
        return yaml.safe_load(hw_path.read_text(encoding="utf-8")) or {}
    return {"device_id": device_id, "claim_boundary": "manifest_missing_use_harness_defaults"}


def evaluate_firmware_compatibility(
    device_id: str,
    probe_output: dict[str, Any] | None = None,
    *,
    mode: str = "",
    consent: bool = False,
    guardian_approved: bool = False,
    marshal_control: bool = False,
    dock_attached: bool | None = None,
) -> dict[str, Any]:
    manifest = load_firmware_manifest(device_id)
    profile = load_device_profile(device_id)
    probe_output = probe_output or {}

    warnings: list[str] = []
    blockers: list[str] = []
    fallbacks: list[str] = []
    evidence = ["physical_board_validation_pending"]

    iface = check_interfaces(manifest)
    descriptors = match_descriptors(device_id, manifest)
    boot = check_boot_readiness(device_id, manifest)

    implemented = list(iface["implemented_interfaces"])
    missing = list(iface["missing_interfaces"])

    # Probe aggregation
    probes = probe_output.get("probes") or {}
    probe_failures = [k for k, v in probes.items() if v.get("status") == "fail"]
    if probe_failures:
        warnings.append(f"Host probes reported fail: {', '.join(probe_failures)}")

    # Dock missing handling
    dock_supported = bool((manifest.get("hardware_interfaces") or {}).get("dock"))
    profile_dock = profile.raw.get("dock", {}).get("supported", False)
    if dock_supported or profile_dock:
        dock_probe = probes.get("dock", {})
        if dock_attached is False:
            warnings.append("Dock expected but not attached — external display may be unavailable")
            fallbacks.append("internal_display_only")
        elif dock_probe.get("status") == "warn" and dock_attached is None:
            warnings.append("Dock hotplug not confirmed on host — use fixture for dock scenarios")

    # Wearables developer mode block
    if device_id == "wearables_arena_set" and mode == "Developer":
        blockers.append("Unrestricted developer mode not allowed on wearables/arena firmware profile")
        fallbacks.append("marshal_controlled_arcade")
        if "developer_firmware_unlock" not in implemented:
            missing.append("developer_firmware_unlock")

    # Research consent
    research_modes = ("Research Measurement", "Laboratory")
    if mode in research_modes and not consent:
        blockers.append("Research measurement requires explicit consent")
        fallbacks.append("offline")
        evidence.append("edge_io_consent_flow_validation")

    # Guardian for restricted modes on student device
    if device_id == "student_14_5" and mode in ("Admin", "Developer") and not guardian_approved:
        if mode == "Admin":
            warnings.append("Admin mode should use guardian approval on student devices")

    # Arena marshal control
    if device_id == "wearables_arena_set" and mode in ("Play", "Arcade") and not marshal_control:
        warnings.append("Arena play should use marshal/admin controls in venue settings")

    # Missing interface contracts
    if missing:
        blockers.append(f"Missing firmware interface contracts: {', '.join(missing)}")

    # Descriptor gaps
    if descriptors.get("missing"):
        warnings.append(f"Descriptor stubs missing: {', '.join(descriptors['missing'])}")

    if not boot.get("boot_ready_harness"):
        blockers.append("Harness boot readiness check failed")

    if probe_output.get("host_environment"):
        warnings.append("Evaluation used host environment probes — not physical gunnchOS board")

    compatible = len(blockers) == 0
    status = "pass" if compatible and not warnings else ("warn" if compatible else "fail")

    return {
        "device_id": device_id,
        "compatible": compatible,
        "status": status,
        "implemented_interfaces": implemented,
        "missing_interfaces": missing,
        "warnings": warnings,
        "blockers": blockers,
        "fallbacks": fallbacks,
        "evidence_required": sorted(set(evidence)),
        "manifest_version": manifest.get("firmware_version"),
        "boot_readiness": boot,
        "descriptor_match": descriptors,
        "probe_summary": {
            "host_os": probe_output.get("host_os"),
            "host_environment": probe_output.get("host_environment", True),
            "probe_count": len(probes),
        },
        "capsule_update_simulated": stage_capsule(device_id).get("status") == "success",
        "claim_boundary": (
            "Firmware compatibility harness — host/emulated validation only; "
            "physical-board validation pending."
        ),
    }
