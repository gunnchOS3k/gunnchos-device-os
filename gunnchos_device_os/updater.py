"""Update probes — Device OS channel metadata + Learning OS honesty.

Learning OS rollback_supported is NOT claimed here; that comes from
LearningOsPackageLifecycle (real prior version). Mock rollback.py must not
be surfaced as supported rollback.
"""
from __future__ import annotations

MANIFEST = {
    "version": "0.1.0-evt1-alpha",
    "signed": "PLACEHOLDER_SIGNATURE_REQUIRES_ENGINEERING_REVIEW",
    "channel": "evt-alpha",
    "staged_rollout_percent": 10,
}

LEARNING_OS_MANIFEST = {
    "version": "0.1.0",
    "channel": "gate-c-digital",
    "signed": False,
    "signing_truth": "UNSIGNED_DIGITAL_FIXTURE",
    "update_owner": "platform_tauri_bundle_via_device_os_package_manager",
    "bundle_id": "com.gunnchos.waike.learning",
    # Probe metadata only — real rollback_supported comes from package lifecycle.
    "rollback_supported": False,
}


def check_for_update(current: str) -> dict:
    latest = MANIFEST["version"]
    return {
        "current": current,
        "latest": latest,
        "update_available": current != latest,
        "signed": MANIFEST["signed"],
        "channel": MANIFEST["channel"],
    }


def check_learning_os_update(current: str) -> dict:
    """Digital Learning OS update probe — not production OTA signing."""
    latest = LEARNING_OS_MANIFEST["version"]
    return {
        "current": current,
        "latest": latest,
        "update_available": current != latest,
        "channel": LEARNING_OS_MANIFEST["channel"],
        "signed": LEARNING_OS_MANIFEST["signed"],
        "signing_truth": LEARNING_OS_MANIFEST["signing_truth"],
        "update_owner": LEARNING_OS_MANIFEST["update_owner"],
        "bundle_id": LEARNING_OS_MANIFEST["bundle_id"],
        "rollback_supported": False,
        "claim_boundary": (
            "Update channel probe only. rollback_supported requires "
            "LearningOsPackageLifecycle prior version — not mock rollback.py."
        ),
    }
