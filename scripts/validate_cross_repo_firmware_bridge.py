#!/usr/bin/env python3
"""Validate cross-repo firmware bridge sync and fallback behavior."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cross_repo_firmware_bridge.sync_firmware_contracts import sync_contracts

REQUIRED_DOCS = [
    "cross_repo_firmware_bridge/README.md",
    "cross_repo_firmware_bridge/HARDWARE_REPO_FIRMWARE_SOURCE_MAP.md",
    "cross_repo_firmware_bridge/FIRMWARE_ARTIFACT_IMPORT_PLAN.md",
    "cross_repo_firmware_bridge/FIRMWARE_CONTRACT_SYNC_STATUS.md",
]


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_DOCS:
        if not (ROOT / rel).exists():
            errors.append(f"Missing doc: {rel}")

    imported = ROOT / "firmware_compat/imported_hardware_contracts"
    if not imported.exists():
        errors.append("Missing imported_hardware_contracts directory")

    manifests = list((imported / "manifests").glob("*_firmware_manifest.yaml")) if imported.exists() else []
    if len(manifests) < 4:
        errors.append(f"Expected 4 firmware manifests, found {len(manifests)}")

    # Fallback path must work without hardware repo
    missing_repo = ROOT / "_nonexistent_hardware_repo_for_test"
    report = sync_contracts(missing_repo, allow_fallback=True)
    if report["status"] != "ok":
        errors.append(f"Fallback sync failed: {report['errors']}")
    if not report.get("fallback_used"):
        errors.append("Expected fallback_used when hardware repo missing")

    report_path = ROOT / "results/firmware_contract_sync_report.json"
    if not report_path.exists():
        errors.append("Missing firmware_contract_sync_report.json")

    # Strict mode should fail without repo and without fallback - we have fallback files so test copy
    if errors:
        print("VALIDATE_CROSS_REPO_FIRMWARE_BRIDGE FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("validate_cross_repo_firmware_bridge: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
