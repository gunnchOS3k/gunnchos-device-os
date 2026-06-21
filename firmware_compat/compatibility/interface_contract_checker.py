"""Validate firmware interface contracts against manifest hardware_interfaces."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
INTERFACES_DIR = ROOT / "firmware_compat" / "imported_hardware_contracts" / "interfaces"

INTERFACE_MAP = {
    "display": "display_enumeration_contract.yaml",
    "input": "input_device_contract.yaml",
    "battery": "battery_status_contract.yaml",
    "thermal": "thermal_sensor_contract.yaml",
    "storage": "storage_enumeration_contract.yaml",
    "network": "network_enumeration_contract.yaml",
    "dock": "docking_external_display_contract.yaml",
    "external_display": "docking_external_display_contract.yaml",
    "power_state": "power_state_contract.yaml",
}


def _load_contract(name: str) -> dict[str, Any] | None:
    path = INTERFACES_DIR / name
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def check_interfaces(manifest: dict[str, Any]) -> dict[str, Any]:
    hw = manifest.get("hardware_interfaces") or {}
    implemented: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []

    for key, spec in hw.items():
        if not spec:
            continue
        contract_name = INTERFACE_MAP.get(key)
        if not contract_name:
            warnings.append(f"No interface map for hardware_interfaces.{key}")
            continue
        contract = _load_contract(contract_name)
        if contract:
            implemented.append(contract.get("interface_id") or key)
        else:
            missing.append(contract_name)

    # Always expect edge_io if research features in OS profile
    edge = _load_contract("edge_io_contract.yaml")
    if edge:
        implemented.append(edge.get("interface_id", "edge_io"))

    status = "fail" if missing else ("warn" if warnings else "pass")
    return {
        "status": status,
        "implemented_interfaces": sorted(set(implemented)),
        "missing_interfaces": missing,
        "warnings": warnings,
    }
