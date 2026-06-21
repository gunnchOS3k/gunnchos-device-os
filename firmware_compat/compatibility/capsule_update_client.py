"""Simulated capsule firmware update client — never flashes real firmware."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    ROOT.parent
    / "gunnchos-hardware-industrial-design"
    / "firmware"
    / "capsule_update"
    / "sample_capsule_manifest.yaml"
)
LOCAL_MANIFEST = ROOT / "firmware_compat" / "fixtures" / "sample_capsule_update_response.json"


def load_capsule_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or DEFAULT_MANIFEST
    if manifest_path.suffix == ".json":
        import json
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest_path.exists():
        return yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    fallback = ROOT / "firmware_compat" / "imported_hardware_contracts" / "capsule_update" / "sample_capsule_manifest.yaml"
    if fallback.exists():
        return yaml.safe_load(fallback.read_text(encoding="utf-8")) or {}
    return {"simulated_only": True, "capsule_id": "missing-manifest-stub"}


def stage_capsule(
    device_id: str,
    *,
    manifest_path: Path | None = None,
    current_version: str = "0.1.0-harness",
) -> dict[str, Any]:
    manifest = load_capsule_manifest(manifest_path)
    if manifest.get("device_id") and manifest["device_id"] != device_id:
        return {
            "status": "fail",
            "device_id": device_id,
            "error": f"Capsule targets {manifest['device_id']}, not {device_id}",
            "simulated_only": True,
        }
    if not manifest.get("simulated_only", True):
        return {
            "status": "fail",
            "device_id": device_id,
            "error": "Refusing non-simulated capsule",
            "simulated_only": False,
        }
    target = manifest.get("target_version", "0.1.1-harness")
    return {
        "status": "success",
        "device_id": device_id,
        "simulated_only": True,
        "capsule_id": manifest.get("capsule_id"),
        "current_version": current_version,
        "target_version": target,
        "reboot_required": True,
        "rollback_supported": manifest.get("rollback_supported", True),
        "message": "Simulated capsule staged — no real firmware flashed",
        "claim_boundary": "Capsule simulation only — physical flash not performed",
    }
