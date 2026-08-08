"""Tests for bootable reference image digital pass."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.bootable_image import (
    TOKEN_DIGITAL_PASS,
    TOKEN_PHYSICAL_PENDING,
    BootableReferenceBuilder,
    QemuBootHarness,
    validate_boot_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "os_build" / "bootable_reference" / "overlay"


def test_overlay_has_supervised_services_and_ipc_client():
    assert (OVERLAY / "init").exists()
    services = OVERLAY / "opt" / "gunnchos" / "services"
    required = [
        "hal",
        "input",
        "ring",
        "display",
        "dock",
        "continuity",
        "identity",
        "permissions",
        "sandbox",
        "connectivity",
        "ai_interface",
        "profile_manager",
        "a11y",
        "diagnostics",
        "updater",
        "recovery",
        "fleet_agent",
    ]
    for sid in required:
        script = (services / f"{sid}.sh").read_text(encoding="utf-8")
        assert "svc_dispatch" in script, sid
        assert "stub supervisor" not in script.lower(), sid
    lib = (services / "_lib.sh").read_text(encoding="utf-8")
    assert "svc_daemon_loop" in lib
    assert "supervised" in lib.lower() or "mailbox" in lib
    assert (OVERLAY / "opt" / "gunnchos" / "bin" / "gunnchos-ipc").exists()
    init = (OVERLAY / "init").read_text(encoding="utf-8")
    assert "GUNNCHOS_SERVICES_KIND=supervised_real" in init
    assert "GUNNCHOS_IPC" in init
    assert "FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE=false" in init
    assert (OVERLAY / "opt" / "gunnchos" / "bin" / "gunnchos-shell").exists()
    assert (OVERLAY / "opt" / "gunnchos" / "apps" / "manifest.json").exists()
    assert (OVERLAY / "opt" / "gunnchos" / "games" / "manifest.json").exists()
    assert (OVERLAY / "opt" / "gunnchos" / "updater" / "ab_status.sh").exists()
    assert (OVERLAY / "opt" / "gunnchos" / "recovery" / "self_check.sh").exists()


def test_overlay_has_required_services_and_init():
    test_overlay_has_supervised_services_and_ipc_client()


def test_build_bootable_initramfs():
    builder = BootableReferenceBuilder()
    result = builder.build(fetch=True)
    assert result["ok"] is True
    assert result["bootable"] is True
    assert result["production_keys_used"] is False
    initramfs = Path(result["initramfs"])
    kernel = Path(result["kernel"])
    assert initramfs.exists() and initramfs.stat().st_size > 1000
    assert kernel.exists() and kernel.stat().st_size > 1000
    manifest = json.loads((builder.paths.artifacts / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["bootable"] is True
    assert manifest["physical_boot_claimed"] is False
    assert manifest["production_keys_used"] is False


def test_qemu_boot_earns_digital_pass():
    builder = BootableReferenceBuilder()
    builder.build(fetch=True)
    evidence = QemuBootHarness(builder.paths).boot(timeout_sec=240.0)
    assert evidence["ok"] is True, evidence.get("markers_missing")
    assert evidence["token"] == TOKEN_DIGITAL_PASS
    assert TOKEN_PHYSICAL_PENDING in evidence["status_tokens"]
    assert evidence["physical_boot_claimed"] is False
    assert evidence["production_keys_used"] is False
    assert evidence["full_operational_product_claimed"] is False
    log_path = ROOT / evidence["log_path"]
    assert log_path.exists()
    text = log_path.read_text(encoding="utf-8")
    assert "GUNNCHOS_BOOT_MARKER=OK" in text
    assert "GUNNCHOS_PRODUCTION_KEYS=false" in text
    validation = validate_boot_evidence(evidence)
    assert validation["ok"] is True
    assert validation["token"] == TOKEN_DIGITAL_PASS
