#!/usr/bin/env python3
"""Capsule experience oracle — failure class detector for Android Capsule gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FAILURE_CLASSES = [
    "BRIDGE_ALLOWLIST_VIOLATION",
    "ORIGIN_REJECT",
    "PERMISSION_BYPASS",
    "SILENT_INSTALL_ATTEMPT",
    "BROAD_FS_PERMISSION",
    "ROOT_API_USE",
    "PIXEL_WIPE_REQUIRED",
    "BOOTLOADER_UNLOCK_REQUIRED",
    "SHELL_NOT_PRODUCTION",
    "SESSION_LOSS",
    "GUEST_OVERCLAIM",
]


def evaluate(gates: dict, evidence: dict) -> dict:
    failures: list[str] = []

    if not gates.get("CAPSULE_ANDROID_BRIDGE_SECURITY_PASS"):
        failures.append("BRIDGE_ALLOWLIST_VIOLATION")
    if evidence.get("foreign_origin_accepted"):
        failures.append("ORIGIN_REJECT")
    if evidence.get("permission_bypass"):
        failures.append("PERMISSION_BYPASS")
    if evidence.get("silent_package_install"):
        failures.append("SILENT_INSTALL_ATTEMPT")
    if evidence.get("broad_fs_permission"):
        failures.append("BROAD_FS_PERMISSION")
    if evidence.get("root_api_use") or not gates.get("NO_ROOT_REQUIRED"):
        failures.append("ROOT_API_USE")
    if not gates.get("NO_PIXEL_WIPE_REQUIRED"):
        failures.append("PIXEL_WIPE_REQUIRED")
    if not gates.get("NO_BOOTLOADER_UNLOCK_REQUIRED"):
        failures.append("BOOTLOADER_UNLOCK_REQUIRED")
    if not gates.get("CAPSULE_PRODUCTION_SHELL_REUSED"):
        failures.append("SHELL_NOT_PRODUCTION")
    if not gates.get("CAPSULE_SESSION_RECOVERY_PASS"):
        failures.append("SESSION_LOSS")
    if gates.get("CAPSULE_QEMU_GUEST_BOOT_PASS") and not evidence.get("qemu_boot_observed"):
        failures.append("GUEST_OVERCLAIM")
    if gates.get("CAPSULE_LINUX_DESKTOP_PROVIDER_PASS") and not evidence.get("desktop_surface_observed"):
        failures.append("GUEST_OVERCLAIM")

    parity = bool(gates.get("GUNNCHOS_CAPSULE_EXPERIENCE_PARITY"))
    if failures:
        parity = False

    return {
        "ok": len(failures) == 0,
        "failures": failures,
        "failure_classes_catalog": FAILURE_CLASSES,
        "GUNNCHOS_CAPSULE_EXPERIENCE_PARITY": parity,
        "NEXT_GUNNCHOS_ACTION": "OWNER_PIXEL6A_HANDS_ON_CAPSULE_USABILITY_PASS",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--gates",
        default="artifacts/android_capsule/GATES.json",
        help="Path to gates JSON",
    )
    ap.add_argument(
        "--evidence",
        default="artifacts/android_capsule/ORACLE_EVIDENCE.json",
        help="Path to evidence JSON",
    )
    ap.add_argument(
        "--out",
        default="artifacts/android_capsule/ORACLE_RESULT.json",
        help="Output path",
    )
    args = ap.parse_args()

    gates = json.loads(Path(args.gates).read_text()) if Path(args.gates).exists() else {}
    evidence = json.loads(Path(args.evidence).read_text()) if Path(args.evidence).exists() else {}
    result = evaluate(gates, evidence)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
