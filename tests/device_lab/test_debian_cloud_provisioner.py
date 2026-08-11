"""WP-011R: guest-native Debian cloud-init provisioner — pure/structural tests.

No network access and no QEMU boot here (that is exercised manually with long
timeouts per the mission's `provision_interactive_guest_debian_cloud.py`
entry point). These tests only cover the pure helpers and the manifest/
evidence writers, and assert the honesty invariant: nothing in this module
may hardcode a `*_PASS` token to true.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab.debian_cloud_provisioner import (
    CLAIM_BOUNDARY,
    DEBIAN_ARCH,
    DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST,
    IMAGE_NAME,
    OPTIONAL_APT_PACKAGES,
    REQUIRED_APT_PACKAGES,
    SHIPPING_IMAGE,
    SILICON_EXACT_EMULATION,
    DebianCloudInteractiveGuestProvisioner,
    build_cloud_init_meta_data,
    build_cloud_init_user_data,
    build_qemu_provision_cmd,
    parse_sha512sums,
    select_provision_accel,
)

FORBIDDEN_PASS_TOKENS = (
    "LIVE_GUNNCHOS_VISUAL_PASS",
    "DSXL_DUAL_COMPOSITOR_UX_PASS",
    "RING_TO_REAL_APP_STATE_MUTATION_PASS",
    "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
    "ECO010_SOAK_PASS",
    "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE",
)


def test_claim_labels_honest():
    assert DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST is True
    assert SHIPPING_IMAGE is False
    assert SILICON_EXACT_EMULATION is False
    assert "SHIPPING_IMAGE=false" in CLAIM_BOUNDARY
    # The claim boundary may name the tokens while explaining they are NOT
    # earned by provisioning alone — it must never assert them as true.
    for token in FORBIDDEN_PASS_TOKENS:
        assert f"{token}=true" not in CLAIM_BOUNDARY.replace(" ", "")
        assert f"{token}: true" not in CLAIM_BOUNDARY.lower()


def test_parse_sha512sums_finds_matching_filename_and_ignores_others():
    text = (
        "deadbeef11223344  debian-12-genericcloud-amd64.qcow2\n"
        "cafebabe55667788 *debian-12-genericcloud-arm64.qcow2\n"
        "# a comment\n"
        "\n"
    )
    digest = parse_sha512sums(text, "debian-12-genericcloud-arm64.qcow2")
    assert digest == "cafebabe55667788"
    assert parse_sha512sums(text, "not-present.qcow2") is None


def test_parse_sha512sums_handles_nested_path_prefix():
    text = "aa11bb22  ./sub/dir/debian-12-genericcloud-arm64.qcow2\n"
    digest = parse_sha512sums(text, "debian-12-genericcloud-arm64.qcow2")
    assert digest == "aa11bb22"


def test_build_cloud_init_user_data_contains_required_packages_and_disable_sentinel():
    user_data = build_cloud_init_user_data(
        guest_agent_script="#!/usr/bin/env python3\nprint('agent')\n",
        guest_agent_service="[Unit]\nDescription=agent\n",
        weston_service="[Unit]\nDescription=weston\n",
        weston_ini="[core]\n",
    )
    assert user_data.startswith("#cloud-config")
    for pkg in ("weston", "seatd", "chromium", "pipewire", "libinput-tools", "python3-evdev"):
        assert pkg in REQUIRED_APT_PACKAGES
        assert f"  - {pkg}" in user_data
    # cloud-init must be disabled on subsequent boots so re-provisioning is
    # not required just to boot the already-provisioned disk again.
    assert "touch /etc/cloud/cloud-init.disabled" in user_data
    assert "power_state" in user_data
    assert "mode: poweroff" in user_data
    for token in FORBIDDEN_PASS_TOKENS:
        assert token not in user_data


def test_build_cloud_init_user_data_embeds_optional_packages_best_effort():
    user_data = build_cloud_init_user_data(
        guest_agent_script="x",
        guest_agent_service="x",
        weston_service="x",
        weston_ini="x",
    )
    for pkg in OPTIONAL_APT_PACKAGES:
        assert pkg in user_data
    # Optional packages are installed best-effort (never blocking provision).
    assert "|| true" in user_data


def test_build_cloud_init_meta_data_sets_hostname():
    meta = build_cloud_init_meta_data(instance_id="gunnchos-lab-123")
    assert "instance-id: gunnchos-lab-123" in meta
    assert "gunnchos-interactive-guest" in meta


def test_build_qemu_provision_cmd_uses_uefi_pflash_and_nocloud_smbios(tmp_path: Path):
    cmd = build_qemu_provision_cmd(
        qemu_bin="qemu-system-aarch64",
        edk2_code=tmp_path / "code.fd",
        edk2_vars=tmp_path / "vars.fd",
        disk=tmp_path / "disk.qcow2",
        boot_log=tmp_path / "boot.log",
        pidfile=tmp_path / "qemu.pid",
        monitor_sock=tmp_path / "mon.sock",
        smbios_url="http://10.0.2.2:8080/",
    )
    joined = " ".join(cmd)
    assert "if=pflash,format=raw,readonly=on" in joined
    assert "ds=nocloud-net;s=http://10.0.2.2:8080/" in joined
    assert "if=virtio,format=qcow2" in joined
    assert "-no-reboot" in cmd
    assert "-daemonize" in cmd


def test_select_provision_accel_returns_known_backend():
    accel = select_provision_accel()
    assert accel["accel"] in {"hvf", "kvm", "tcg"}
    assert accel["cpu"]


def test_environment_check_reports_missing_tools_structurally(monkeypatch: pytest.MonkeyPatch):
    import gunnchos_device_os.device_lab.debian_cloud_provisioner as mod

    monkeypatch.setattr(mod, "find_qemu_img", lambda: None)
    monkeypatch.setattr(mod, "find_qemu_system_aarch64", lambda: None)
    monkeypatch.setattr(mod, "find_edk2_firmware", lambda: None)
    provisioner = mod.DebianCloudInteractiveGuestProvisioner(repo_root=Path("/tmp/does-not-matter"))
    # environment_check imports the module-level names directly, so patch
    # via the module the provisioner actually calls through.
    env = provisioner.environment_check()
    assert env["ok"] is False
    assert set(env["missing"]) <= {"qemu-img", "qemu-system-aarch64", "edk2-aarch64-code.fd", "curl"}


def test_finish_writes_manifest_and_evidence_without_claiming_pass_tokens(tmp_path: Path):
    provisioner = DebianCloudInteractiveGuestProvisioner(repo_root=tmp_path)
    evidence = {
        "schema": "gunnchos.device_lab.interactive_guest_debian_cloud_provision.v1",
        "image": {"url": "https://example.invalid/x.qcow2", "arch": DEBIAN_ARCH},
        "download": {"ok": False, "error": "network_unavailable_in_test"},
    }
    provisioner._finish(evidence, ok=False)

    evidence_path = provisioner.artifacts / "INTERACTIVE_GUEST_PROVISION_EVIDENCE.json"
    manifest_path = provisioner.artifacts / "INTERACTIVE_GUEST_MANIFEST.json"
    assert evidence_path.is_file()
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST"] is True
    assert manifest["SHIPPING_IMAGE"] is False
    assert manifest["SILICON_EXACT_EMULATION"] is False
    assert manifest["provision_ok"] is False
    assert manifest["pass_tokens_earned_by_this_manifest"] == []
    for token in FORBIDDEN_PASS_TOKENS:
        assert manifest.get(token) is not True

    written_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert written_evidence["ok"] is False


def test_finish_manifest_provision_ok_true_still_earns_no_pass_token(tmp_path: Path):
    """A *successful* provision run must still never claim a `*_PASS` token —
    provisioning packages is a precondition for the in-guest proofs, not the
    proof itself."""
    provisioner = DebianCloudInteractiveGuestProvisioner(repo_root=tmp_path)
    disk = provisioner.artifacts / f"interactive-root-{IMAGE_NAME.split('-')[-1].replace('.qcow2', '')}.qcow2"
    evidence = {"image": {"url": "https://example.invalid/x.qcow2"}, "disk": {"path": str(disk)}}
    provisioner._finish(evidence, ok=True)

    manifest = json.loads(
        (provisioner.artifacts / "INTERACTIVE_GUEST_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["provision_ok"] is True
    assert manifest["pass_tokens_earned_by_this_manifest"] == []
    for token in FORBIDDEN_PASS_TOKENS:
        assert manifest.get(token) is not True
    assert set(manifest["required_packages"]) >= set(REQUIRED_APT_PACKAGES)
    for cmd in ("framebuffer_capture", "compositor_info", "app_launch"):
        assert cmd in manifest["guest_agent_commands"]
