"""Service catalog and matrix for the digital runtime."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.runtime.adapters import SERVICE_CLASSES
from gunnchos_device_os.runtime.service_base import CLAIM_BOUNDARY


# Ordered for documentation; supervisor topological-sorts at start.
SERVICE_CATALOG: dict[str, dict[str, Any]] = {
    "hal": {
        "title": "Hardware Abstraction Layer",
        "module": "gunnchos_device_os.hardware_abstraction",
        "deps": [],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "input": {
        "title": "Input Mapper",
        "module": "gunnchos_device_os.input_mapper",
        "deps": ["hal"],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "ring": {
        "title": "Ring Input Adapter",
        "module": "ring_input / runtime stub",
        "deps": ["input"],
        "maturity": "digital_stub",
        "persistence": "optional",
        "fault_injection": True,
        "notes": "Physical ring pending; software fallback path only",
    },
    "display": {
        "title": "Display Manager",
        "module": "gunnchos_device_os.display_manager",
        "deps": ["hal"],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "dock": {
        "title": "Dock Service",
        "module": "gunnchos_device_os.dock",
        "deps": ["display", "hal"],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "identity": {
        "title": "Unified Identity",
        "module": "gunnchos_device_os.unified_identity",
        "deps": [],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "continuity": {
        "title": "Dock Continuity",
        "module": "gunnchos_device_os.dock.continuity",
        "deps": ["dock", "identity", "display"],
        "maturity": "digital_integrated",
        "persistence": "session_snapshot",
        "fault_injection": True,
    },
    "permissions": {
        "title": "Permissions Manager",
        "module": "gunnchos_device_os.permissions_manager",
        "deps": ["identity"],
        "maturity": "digital_integrated",
        "persistence": "in_memory_grants",
        "fault_injection": True,
    },
    "sandbox": {
        "title": "Sandbox Policy",
        "module": "gunnchos_device_os.sandbox_policy",
        "deps": ["permissions"],
        "maturity": "digital_integrated",
        "persistence": "profiles",
        "fault_injection": True,
        "notes": "Software policy only — not kernel seccomp",
    },
    "diagnostics": {
        "title": "Diagnostics Log",
        "module": "gunnchos_device_os.diagnostics_log",
        "deps": [],
        "maturity": "digital_integrated",
        "persistence": "jsonl",
        "fault_injection": True,
    },
    "updater": {
        "title": "OTA Updater / Rollback",
        "module": "gunnchos_device_os.ota_state_machine",
        "deps": ["diagnostics"],
        "maturity": "digital_integrated",
        "persistence": "slot_state",
        "fault_injection": True,
        "notes": "Simulation only; no live channel; no production signing",
    },
    "recovery": {
        "title": "Recovery Playbook",
        "module": "gunnchos_device_os.boot.recovery",
        "deps": ["updater", "diagnostics"],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "connectivity": {
        "title": "Connectivity Orchestrator",
        "module": "gunnchos_device_os.connectivity_orchestrator",
        "deps": ["diagnostics"],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
        "notes": "No carrier attach claim",
    },
    "profile_manager": {
        "title": "Profile Manager",
        "module": "gunnchos_device_os.profile_manager + runtime_profiles",
        "deps": ["identity", "hal"],
        "maturity": "digital_integrated",
        "persistence": "optional",
        "fault_injection": True,
    },
    "ai_interface": {
        "title": "AI Interface",
        "module": "gunnchos_device_os.gunnchai_integration",
        "deps": ["permissions", "diagnostics", "profile_manager"],
        "maturity": "digital_stub",
        "persistence": "session_counters",
        "fault_injection": True,
        "notes": "Local privacy mode default; tutor mock safety checks",
    },
    "a11y": {
        "title": "Accessibility",
        "module": "gunnchos_device_os.accessibility_manager",
        "deps": ["display", "input", "profile_manager"],
        "maturity": "digital_integrated",
        "persistence": "settings",
        "fault_injection": True,
    },
    "fleet_agent": {
        "title": "Fleet Agent (DEV)",
        "module": "gunnchos_device_os.runtime.adapters.FleetAgentService",
        "deps": ["identity", "diagnostics", "updater", "connectivity"],
        "maturity": "digital_stub",
        "persistence": "enrollment_state",
        "fault_injection": True,
        "notes": "DEV enrollment tokens only; not MDM; no production keys",
    },
}


REQUIRED_SERVICE_IDS = (
    "hal",
    "input",
    "ring",
    "display",
    "dock",
    "continuity",
    "identity",
    "permissions",
    "sandbox",
    "updater",
    "recovery",
    "diagnostics",
    "connectivity",
    "ai_interface",
    "profile_manager",
    "a11y",
    "fleet_agent",
)


def service_matrix() -> dict[str, Any]:
    rows = []
    for sid in REQUIRED_SERVICE_IDS:
        meta = SERVICE_CATALOG[sid]
        cls = SERVICE_CLASSES[sid]
        rows.append(
            {
                "service_id": sid,
                "title": meta["title"],
                "deps": list(meta["deps"]),
                "class_deps": list(cls.dependencies),
                "api_surface": list(cls.api_surface),
                "maturity": meta["maturity"],
                "persistence": meta["persistence"],
                "fault_injection": meta["fault_injection"],
                "module": meta["module"],
                "notes": meta.get("notes"),
                "adapter_registered": True,
            }
        )
    missing = [s for s in REQUIRED_SERVICE_IDS if s not in SERVICE_CLASSES]
    return {
        "schema": "gunnchos.runtime.service_matrix.v1",
        "services": rows,
        "count": len(rows),
        "required_count": len(REQUIRED_SERVICE_IDS),
        "missing": missing,
        "all_present": not missing,
        "token": "GUNNCHOS_RUNTIME_SERVICE_MATRIX_DIGITAL_PASS" if not missing else None,
        "full_operational_product_claimed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
