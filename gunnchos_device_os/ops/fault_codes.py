"""Support fault-code catalog — software taxonomy only.

Codes classify digital diagnostics. They do not certify a physical root
cause or a warranty outcome.
"""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.ops.claim import CLAIM_BOUNDARY

CATALOG: dict[str, dict[str, str]] = {
    "FC-BOOT-001": {"subsystem": "boot", "summary": "device failed to reach recovery/launcher", "severity": "high"},
    "FC-BATT-001": {"subsystem": "battery", "summary": "battery health or charge-path fault", "severity": "high"},
    "FC-DISP-001": {"subsystem": "display", "summary": "panel bring-up or touch self-test fail", "severity": "high"},
    "FC-STOR-001": {"subsystem": "storage", "summary": "storage not writable or image slot unfit", "severity": "high"},
    "FC-NET-001": {"subsystem": "network", "summary": "no bearer / captive / DNS fail", "severity": "medium"},
    "FC-UPD-001": {"subsystem": "update", "summary": "A/B update verify or rollback path fail", "severity": "high"},
    "FC-RING-001": {"subsystem": "ring", "summary": "authenticated ring pair/input fail", "severity": "medium"},
    "FC-DOCK-001": {"subsystem": "dock", "summary": "dock detect or display-mode fail", "severity": "medium"},
    "FC-AI-001": {"subsystem": "ai", "summary": "local AI runtime unavailable", "severity": "low"},
    "FC-PRIV-001": {"subsystem": "privacy", "summary": "privacy/consent gate blocked an action", "severity": "low"},
    "FC-ID-001": {"subsystem": "identity", "summary": "device identity/cert request incomplete", "severity": "high"},
    "FC-WIPE-001": {"subsystem": "wipe", "summary": "secure wipe did not complete", "severity": "high"},
}


def lookup(code: str) -> dict[str, Any]:
    entry = CATALOG.get(code)
    if entry is None:
        return {"ok": False, "error": "unknown_fault_code", "code": code}
    return {"ok": True, "code": code, **entry, "claim_boundary": CLAIM_BOUNDARY}


def list_codes() -> list[str]:
    return sorted(CATALOG)
