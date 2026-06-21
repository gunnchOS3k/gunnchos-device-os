"""Harness boot readiness checker — not physical hardware boot."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.hardware_boot_readiness import evaluate_boot_readiness


def check_boot_readiness(device_id: str, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or {}
    sim = evaluate_boot_readiness(device_id)
    boot_paths = manifest.get("supported_boot_paths") or []
    checks = dict(sim.get("checks") or {})
    checks["firmware_manifest_loaded"] = bool(manifest)
    checks["uefi_boot_path_documented"] = "uefi_standard_boot" in boot_paths or not boot_paths
    checks["recovery_path_documented"] = "recovery_boot" in boot_paths or not boot_paths
    ready = all(checks.values())
    return {
        "device_id": device_id,
        "boot_ready_harness": ready,
        "checks": checks,
        "status": "simulated",
        "claim_boundary": sim.get("claim_boundary"),
        "user_message": sim.get("user_message"),
    }
