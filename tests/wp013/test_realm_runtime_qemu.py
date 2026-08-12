"""WP-013R realm runtime — QEMU boot of EVT/FACTORY/RECOVERY artifacts."""
from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.realm_runtime import (
    boot_realm_runtime,
    verify_all_realm_runtimes,
)

ROOT = Path(__file__).resolve().parents[2]


def _qemu_and_assets_available() -> bool:
    kernel = ROOT / "os_build" / "bootable_reference" / "artifacts" / "vmlinuz-virt"
    alpine = (
        ROOT
        / "os_build"
        / "bootable_reference"
        / "cache"
        / "alpine-minirootfs-aarch64.tar.gz"
    )
    try:
        from gunnchos_device_os.release_engineering.realm_runtime import _qemu_bin

        _qemu_bin()
    except Exception:
        return False
    return kernel.exists() and alpine.exists()


@pytest.mark.skipif(not _qemu_and_assets_available(), reason="qemu/kernel/alpine cache missing")
def test_recovery_realm_qemu_runtime_boot():
    evidence = boot_realm_runtime(repo_root=ROOT, alias="recovery", timeout_sec=90.0)
    assert evidence.get("attempted") is True
    assert evidence.get("mode") == "qemu_realm_rootfs_overlay_boot"
    assert evidence.get("ok") is True, evidence.get("markers_missing")
    assert evidence.get("PRODUCTION_RELEASE_CLAIMED") is False


@pytest.mark.skipif(not _qemu_and_assets_available(), reason="qemu/kernel/alpine cache missing")
def test_all_realm_runtimes_earn_tokens():
    result = verify_all_realm_runtimes(ROOT, timeout_sec=90.0)
    assert result["IMAGE_REALM_POLICY_SEPARATION_PASS"] is True
    assert result["IMAGE_REALM_BEHAVIORAL_SEPARATION_PASS"] is True
    assert result["EVT_IMAGE_RUNTIME_PASS"] is True
    assert result["FACTORY_IMAGE_RUNTIME_PASS"] is True
    assert result["RECOVERY_IMAGE_RUNTIME_PASS"] is True
    assert result.get("PRODUCTION_RELEASE_CLAIMED") is not True
    fps = result.get("behavior_fingerprints") or {}
    assert fps.get("evt", "").startswith("evt:")
    assert fps.get("factory", "").startswith("factory:")
    assert fps.get("recovery", "").startswith("recovery:")
    assert len(set(fps.values())) == 3
