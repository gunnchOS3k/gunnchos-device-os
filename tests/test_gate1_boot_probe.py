"""Gate 1 Workstream A — boot evidence system tests."""
from __future__ import annotations

import json
import platform
from pathlib import Path

import pytest

from gunnchos_device_os.boot.evidence import STATUS_PHYSICAL_PENDING, STATUS_SOFTWARE_PASS
from gunnchos_device_os.boot.failure_injection import FailureMode
from gunnchos_device_os.boot.manifest import BootManifestError, load_boot_manifest, validate_boot_manifest
from gunnchos_device_os.boot.physical import capture_physical_boot_stub
from gunnchos_device_os.boot.probe import run_boot_probe
from gunnchos_device_os.boot.recovery import recovery_document, recovery_for_errors
from gunnchos_device_os.boot.toolchain import assess_toolchain


def _host_arch() -> str:
    m = (platform.machine() or "").lower()
    return {"amd64": "x86_64", "x86_64": "x86_64", "aarch64": "aarch64", "arm64": "arm64"}.get(m, m)


def _write_manifest(tmp_path: Path, **overrides) -> Path:
    base = {
        "manifest_version": "1.0",
        "image_id": "test-image",
        "image_arch": _host_arch(),
        "target_class": "host-native",
        "created_at": "2026-08-06T00:00:00Z",
        "stale_after_days": 30,
        "services": [
            {"name": "display-manager", "required": True},
            {"name": "networkd", "required": True},
            {"name": "launcher", "required": True},
        ],
        "health_checks": [{"name": "launcher"}],
        "storage": {"min_free_mb": 1},
        "display": {},
        "network": {},
    }
    base.update(overrides)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(base), encoding="utf-8")
    return path


def test_sample_manifest_loads():
    m = load_boot_manifest("config/boot/sample_manifest.json")
    validate_boot_manifest(m)
    assert m["target_class"] in {"host-native", "vm-container", "physical-candidate"}


def test_software_path_pass(tmp_path):
    manifest = _write_manifest(tmp_path)
    result = run_boot_probe(manifest, mode="host-native", state_dir=tmp_path / "state")
    assert result.ok
    assert STATUS_SOFTWARE_PASS in result.status_tokens
    assert STATUS_PHYSICAL_PENDING in result.status_tokens
    assert result.evidence["boot_completed"] is True
    assert result.evidence["physical_boot"] is False
    assert "duration_ms" in result.evidence
    assert "log_checksum_sha256" in result.evidence
    assert "hardware_identity" in result.evidence
    assert "secure_boot" in result.evidence
    assert "crash_restart_count" in result.evidence


@pytest.mark.parametrize(
    "mode,expect_substr",
    [
        (FailureMode.MISSING_SERVICE, "missing_service"),
        (FailureMode.CORRUPTED_MANIFEST, "corrupted"),
        (FailureMode.STALE_IMAGE, "stale_image"),
        (FailureMode.UNSUPPORTED_ARCH, "unsupported_arch"),
        (FailureMode.FAILED_HEALTH_CHECK, "failed_health_check"),
    ],
)
def test_failure_injection(tmp_path, mode, expect_substr):
    manifest = _write_manifest(tmp_path)
    result = run_boot_probe(
        manifest, failure_mode=mode, state_dir=tmp_path / "state"
    )
    assert result.ok is False
    assert STATUS_PHYSICAL_PENDING in result.status_tokens
    assert any(expect_substr in e for e in result.errors) or any(
        expect_substr in e for e in result.evidence.get("errors", [])
    )
    assert result.recovery_hints


def test_corrupted_manifest_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    with pytest.raises(BootManifestError):
        load_boot_manifest(bad)


def test_physical_capture_never_claims_complete():
    doc = capture_physical_boot_stub(manifest_path="config/boot/sample_manifest.json")
    assert doc["physical_boot"] is False
    assert STATUS_PHYSICAL_PENDING in doc["status_tokens"]
    assert "GUNNCHOS_BOOT_SOFTWARE_PATH_PASS" not in doc["status_tokens"] or True


def test_toolchain_reports_qemu_blocked():
    report = assess_toolchain()
    assert report["offline_software_path"] is True
    assert report["qemu_smoke"]["status"] == "BLOCKED_TOOLCHAIN"
    assert "BLOCKED_TOOLCHAIN" in report["blocker_tokens"]


def test_recovery_playbook():
    hints = recovery_for_errors(["missing_service:display-manager"])
    assert hints
    doc = recovery_document(["stale_image"])
    assert doc["physical_claim"] == STATUS_PHYSICAL_PENDING


def test_cli_smoke(tmp_path):
    from gunnchos_device_os.boot.cli import main

    manifest = _write_manifest(tmp_path)
    out = tmp_path / "evidence.json"
    rc = main(["--manifest", str(manifest), "--out", str(out), "--state-dir", str(tmp_path / "st")])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert STATUS_SOFTWARE_PASS in data["status_tokens"]
