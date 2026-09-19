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
    "BLACK_SCREEN_NO_RENDER",
    "JS_BUNDLE_CORS_BLOCK",
    "MAIN_DOCUMENT_FAIL",
    "SHELL_READY_TIMEOUT",
    "DOM_PROOF_MISSING",
    "PHYSICAL_HOME_NOT_RENDERED",
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
    if gates.get("CAPSULE_SESSION_RECOVERY_PASS") is False and evidence.get("session_loss"):
        failures.append("SESSION_LOSS")
    if gates.get("CAPSULE_QEMU_GUEST_BOOT_PASS") and not evidence.get("qemu_boot_observed"):
        failures.append("GUEST_OVERCLAIM")
    if gates.get("CAPSULE_LINUX_DESKTOP_PROVIDER_PASS") and not evidence.get("desktop_surface_observed"):
        failures.append("GUEST_OVERCLAIM")

    # Physical render chain
    if evidence.get("cors_blocked_after_appassets") or (
        evidence.get("cors_blocked_file_origin") and not evidence.get("render_recovered")
    ):
        failures.append("JS_BUNDLE_CORS_BLOCK")
    if evidence.get("main_document_failed"):
        failures.append("MAIN_DOCUMENT_FAIL")
    if evidence.get("shell_ready_timeout"):
        failures.append("SHELL_READY_TIMEOUT")
    if gates.get("CAPSULE_PIXEL_RENDER_PASS") and not evidence.get("dom_proof_home"):
        failures.append("DOM_PROOF_MISSING")
    if gates.get("CAPSULE_PIXEL_RENDER_PASS") and not evidence.get("home_screenshot_pass"):
        failures.append("PHYSICAL_HOME_NOT_RENDERED")
    if evidence.get("black_screen_observed") and not evidence.get("render_recovered"):
        failures.append("BLACK_SCREEN_NO_RENDER")

    # Physical gates cannot be true without full chain
    if gates.get("CAPSULE_PIXEL_RENDER_PASS") and not all(
        [
            evidence.get("main_document_ok"),
            evidence.get("js_bundle_ok"),
            evidence.get("react_mount_ok"),
            evidence.get("dom_proof_home"),
            evidence.get("home_screenshot_pass"),
        ]
    ):
        failures.append("PHYSICAL_HOME_NOT_RENDERED")

    parity = bool(gates.get("GUNNCHOS_CAPSULE_EXPERIENCE_PARITY"))
    if failures:
        parity = False
    if not gates.get("CAPSULE_PHYSICAL_P0_READY"):
        parity = False

    next_action = (
        "OWNER_PIXEL6A_HANDS_ON_CAPSULE_USABILITY_PASS"
        if gates.get("CAPSULE_PIXEL_RENDER_PASS")
        and gates.get("CAPSULE_PIXEL_INTERACTIVE_SHELL_PASS")
        and gates.get("CAPSULE_FULLSCREEN_OS_EXPERIENCE_PASS")
        else "FIX_CAPSULE_PIXEL_RENDER_PATH"
    )

    return {
        "ok": len(failures) == 0,
        "failures": failures,
        "failure_classes_catalog": FAILURE_CLASSES,
        "GUNNCHOS_CAPSULE_EXPERIENCE_PARITY": parity,
        "NEXT_GUNNCHOS_ACTION": next_action,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gates", default="artifacts/android_capsule/GATES.json")
    ap.add_argument("--evidence", default="artifacts/android_capsule/ORACLE_EVIDENCE.json")
    ap.add_argument("--out", default="artifacts/android_capsule/ORACLE_RESULT.json")
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
