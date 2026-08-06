"""Boot probe: record completion, duration, health, storage, I/O, network, identity."""
from __future__ import annotations

import os
import platform
import shutil
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from gunnchos_device_os.identity import (
    new_boot_id,
    sha256_file,
    sha256_json,
    stable_hardware_identity,
    utc_now_iso,
)

from .failure_injection import FailureMode, apply_failure
from .manifest import BootManifestError, load_boot_manifest


@dataclass
class BootProbeResult:
    ok: bool
    status_tokens: list[str]
    evidence: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    recovery_hints: list[str] = field(default_factory=list)


def _host_arch() -> str:
    m = (platform.machine() or "").lower()
    aliases = {"x86_64": "x86_64", "amd64": "x86_64", "aarch64": "aarch64", "arm64": "aarch64"}
    return aliases.get(m, m)


def _arch_compatible(image_arch: str, host_arch: str) -> bool:
    a = image_arch.lower()
    h = host_arch.lower()
    if a in {"amd64", "x86_64"} and h in {"amd64", "x86_64"}:
        return True
    if a in {"arm64", "aarch64"} and h in {"arm64", "aarch64"}:
        return True
    return a == h


def _storage_snapshot(min_free_mb: int) -> dict[str, Any]:
    usage = shutil.disk_usage(Path.cwd())
    free_mb = usage.free // (1024 * 1024)
    return {
        "free_mb": free_mb,
        "total_mb": usage.total // (1024 * 1024),
        "min_free_mb": min_free_mb,
        "ok": free_mb >= min_free_mb,
    }


def _display_input_snapshot() -> dict[str, Any]:
    # Host-native software path: report observability, not physical panel proof.
    display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    return {
        "display_env_present": bool(display),
        "display_env": display or None,
        "input_subsystem": "host-observed",
        "claim": "Software path observes host display/input env only; not physical panel validation.",
    }


def _network_snapshot() -> dict[str, Any]:
    try:
        hostname = socket.gethostname()
        # Resolve without assuming external connectivity.
        addrs = socket.getaddrinfo(hostname, None)
        families = sorted({str(a[0].name) for a in addrs})
        return {"ok": True, "address_families": families, "hostname_resolvable": True}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "hostname_resolvable": False}


def _secure_boot_state() -> dict[str, Any]:
    """Expose secure-boot state only when the host surfaces it."""
    sb_path = Path("/sys/firmware/efi/efivars")
    if not sb_path.exists():
        return {
            "exposed": False,
            "state": "not_exposed",
            "note": "EFI secure-boot variables not visible on this host.",
        }
    markers = list(sb_path.glob("*SecureBoot*"))
    return {
        "exposed": True,
        "state": "efi_vars_present" if markers else "efi_present_no_secureboot_var",
        "var_count_hint": len(markers),
        "verified": False,
        "note": "Exposed state only; not attested measured boot.",
    }


def _service_health(
    services: list[dict[str, Any]],
    *,
    missing: set[str] | None = None,
    fail_health: set[str] | None = None,
) -> list[dict[str, Any]]:
    missing = missing or set()
    fail_health = fail_health or set()
    results = []
    for svc in services:
        name = svc["name"]
        required = bool(svc.get("required", True))
        if name in missing:
            results.append(
                {
                    "name": name,
                    "required": required,
                    "present": False,
                    "healthy": False,
                    "error": "missing_service",
                }
            )
            continue
        healthy = name not in fail_health
        results.append(
            {
                "name": name,
                "required": required,
                "present": True,
                "healthy": healthy,
                "error": None if healthy else "failed_health_check",
            }
        )
    return results


def _crash_restart_count(state_dir: Path) -> int:
    counter = state_dir / "crash_restart_count.txt"
    if not counter.exists():
        return 0
    try:
        return max(0, int(counter.read_text(encoding="utf-8").strip() or "0"))
    except ValueError:
        return 0


def run_boot_probe(
    manifest_path: Path | str,
    *,
    mode: str = "host-native",
    failure_mode: FailureMode | str | None = None,
    state_dir: Path | str | None = None,
    physical: bool = False,
    clock: Callable[[], float] = time.perf_counter,
) -> BootProbeResult:
    """Run software boot probe and emit machine-readable evidence."""
    t0 = clock()
    errors: list[str] = []
    recovery: list[str] = []
    state = Path(state_dir) if state_dir else Path("results/gate1/boot_state")
    state.mkdir(parents=True, exist_ok=True)

    injected = apply_failure(failure_mode)
    manifest_file = Path(manifest_path)

    # Stale / missing image simulation
    if injected.stale_image:
        errors.append("stale_image: manifest image_id marked past stale_after_days")
        recovery.append("Rebuild or refresh the boot image; update image_id and created_at.")

    try:
        if injected.corrupt_manifest:
            raise BootManifestError("corrupted manifest JSON: injected corruption")
        manifest = load_boot_manifest(manifest_file)
    except BootManifestError as exc:
        duration_ms = int((clock() - t0) * 1000)
        evidence = {
            "schema": "gunnchos.boot_evidence.v1",
            "boot_id": new_boot_id(),
            "timestamp": utc_now_iso(),
            "mode": mode,
            "boot_completed": False,
            "duration_ms": duration_ms,
            "errors": [str(exc)],
            "status_tokens": [
                "GUNNCHOS_BOOT_SOFTWARE_PATH_FAIL",
                "GUNNCHOS_PHYSICAL_BOOT_PENDING",
            ],
            "physical_boot": False,
            "claim_boundary": "Software probe failed; physical boot not claimed.",
        }
        return BootProbeResult(
            ok=False,
            status_tokens=evidence["status_tokens"],
            evidence=evidence,
            errors=[str(exc)],
            recovery_hints=[
                "Validate manifest against schemas/gate1/boot_manifest.schema.json",
                "See docs/gate1/BOOT_RECOVERY.md",
            ],
        )

    if injected.unsupported_arch:
        manifest = dict(manifest)
        manifest["image_arch"] = "riscv64"

    host_arch = _host_arch()
    image_arch = str(manifest["image_arch"])
    if image_arch.lower() == "host":
        image_arch = host_arch
    arch_ok = _arch_compatible(image_arch, host_arch)
    if not arch_ok:
        errors.append(f"unsupported_arch: image={image_arch} host={host_arch}")
        recovery.append("Use a matching arch image or run under a compatible emulator/VM.")

    # Stale check from manifest metadata
    stale_after = int(manifest.get("stale_after_days", 0) or 0)
    if injected.stale_image or (stale_after < 0):
        # stale_after < 0 used in fixtures to force stale
        if "stale_image" not in "".join(errors):
            errors.append("stale_image: image exceeded freshness policy")
            recovery.append("Refresh boot image artifacts and regenerate manifest.")

    services = _service_health(
        list(manifest["services"]),
        missing=injected.missing_services,
        fail_health=injected.failed_health_checks,
    )
    for svc in services:
        if svc["required"] and not svc["present"]:
            errors.append(f"missing_service:{svc['name']}")
            recovery.append(f"Restore required service '{svc['name']}' and re-run probe.")
        elif svc["required"] and not svc["healthy"]:
            errors.append(f"failed_health_check:{svc['name']}")
            recovery.append(f"Inspect logs for '{svc['name']}' and clear health failure.")

    storage = _storage_snapshot(int(manifest["storage"]["min_free_mb"]))
    if not storage["ok"]:
        errors.append("storage_insufficient")
        recovery.append("Free disk space above storage.min_free_mb and retry.")

    display_input = _display_input_snapshot()
    network = _network_snapshot()
    if not network.get("ok"):
        errors.append("network_unhealthy")
        recovery.append("Restore local hostname resolution / loopback networking.")

    hw = stable_hardware_identity()
    secure_boot = _secure_boot_state()
    crash_restarts = _crash_restart_count(state)

    try:
        log_checksum = sha256_file(manifest_file)
    except OSError:
        log_checksum = sha256_json(manifest)

    duration_ms = int((clock() - t0) * 1000)
    boot_completed = len(errors) == 0

    status_tokens = []
    if boot_completed and not physical:
        status_tokens.append("GUNNCHOS_BOOT_SOFTWARE_PATH_PASS")
    elif not boot_completed:
        status_tokens.append("GUNNCHOS_BOOT_SOFTWARE_PATH_FAIL")
    status_tokens.append("GUNNCHOS_PHYSICAL_BOOT_PENDING")

    evidence = {
        "schema": "gunnchos.boot_evidence.v1",
        "boot_id": new_boot_id(),
        "timestamp": utc_now_iso(),
        "mode": mode,
        "target_class": manifest.get("target_class"),
        "image_id": manifest.get("image_id"),
        "image_arch": image_arch,
        "host_arch": host_arch,
        "arch_compatible": arch_ok,
        "boot_completed": boot_completed,
        "duration_ms": duration_ms,
        "services": services,
        "storage": storage,
        "display_input": display_input,
        "network": network,
        "hardware_identity": hw,
        "secure_boot": secure_boot,
        "crash_restart_count": crash_restarts,
        "log_checksum_sha256": log_checksum,
        "failure_injection": injected.label,
        "errors": errors,
        "physical_boot": False,
        "physical_evidence_captured": False,
        "status_tokens": status_tokens,
        "claim_boundary": (
            "Software boot path evidence only. "
            "GUNNCHOS_PHYSICAL_BOOT_PENDING — do not claim physical boot complete."
        ),
    }

    return BootProbeResult(
        ok=boot_completed,
        status_tokens=status_tokens,
        evidence=evidence,
        errors=errors,
        recovery_hints=recovery or ["See docs/gate1/BOOT_RECOVERY.md"],
    )
