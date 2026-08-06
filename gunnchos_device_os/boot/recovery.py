"""Boot recovery instructions keyed by failure class."""
from __future__ import annotations

from typing import Any


RECOVERY_PLAYBOOK: dict[str, list[str]] = {
    "missing_service": [
        "Confirm the service is listed in the boot manifest services[] array.",
        "Restore the missing unit/process and re-run gunnchos-boot-probe.",
        "If optional, mark required=false in the manifest.",
    ],
    "corrupted_manifest": [
        "Replace the manifest with config/boot/sample_manifest.json or a known-good copy.",
        "Validate JSON against schemas/gate1/boot_manifest.schema.json.",
        "Re-run: python -m gunnchos_device_os.boot --manifest <path>",
    ],
    "stale_image": [
        "Rebuild the image artifact and update image_id / created_at.",
        "Reset stale_after_days to a positive freshness window.",
        "Do not claim physical boot from a stale software image.",
    ],
    "unsupported_arch": [
        "Select an image_arch matching the host (x86_64/amd64 or aarch64/arm64).",
        "Or run under a compatible VM/container; QEMU full-system path may be BLOCKED_TOOLCHAIN.",
    ],
    "failed_health_check": [
        "Inspect service logs for the unhealthy unit.",
        "Clear the failure condition, then re-run the probe.",
        "Use --failure-mode none for a clean software-path pass after fix.",
    ],
    "storage_insufficient": [
        "Free disk space above storage.min_free_mb.",
        "Relocate results/ artifacts if the volume is full.",
    ],
    "network_unhealthy": [
        "Verify loopback and local hostname resolution.",
        "Offline software path does not require external internet.",
    ],
    "generic": [
        "See docs/gate1/BOOT_RECOVERY.md.",
        "Keep status GUNNCHOS_PHYSICAL_BOOT_PENDING until physical capture succeeds.",
    ],
}


def recovery_for_errors(errors: list[str]) -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()
    for err in errors:
        key = "generic"
        for prefix in RECOVERY_PLAYBOOK:
            if err.startswith(prefix) or prefix in err:
                key = prefix
                break
        if key not in seen:
            hints.extend(RECOVERY_PLAYBOOK[key])
            seen.add(key)
    if not hints:
        hints.extend(RECOVERY_PLAYBOOK["generic"])
    return hints


def recovery_document(errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "title": "gunnchOS Gate 1 boot recovery",
        "physical_claim": "GUNNCHOS_PHYSICAL_BOOT_PENDING",
        "steps": recovery_for_errors(errors or []),
        "playbook_keys": sorted(RECOVERY_PLAYBOOK.keys()),
    }
