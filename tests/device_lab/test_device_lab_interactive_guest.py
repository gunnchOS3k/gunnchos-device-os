"""WP-011R: Device Lab Interactive Development Guest v1 scaffolding.

Manifest schema + label tests only. Deliberately does NOT assert any
LIVE_GUNNCHOS_VISUAL_PASS / DSXL_DUAL_COMPOSITOR_UX_PASS /
RING_TO_REAL_APP_STATE_MUTATION_PASS / FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS
/ ECO-010 soak PASS, and does not flip any master-complete token. This
scaffolding earns nothing by itself.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab.guest_agent import SUPPORTED_COMMANDS
from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient
from gunnchos_device_os.device_lab.image_builder import DEVICE_LAB_DEVELOPMENT_GUEST
from gunnchos_device_os.device_lab.interactive_image_builder import (
    ARCH_MATRIX,
    DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST,
    INTERACTIVE_GUEST_SCHEMA,
    REQUIRED_PACKAGES,
    SHIPPING_IMAGE,
    InteractiveGuestImageBuilder,
    detect_build_capability,
    interactive_manifest,
)
from gunnchos_device_os.device_lab.virtualization.qemu_guest import (
    INTERACTIVE_GUEST_ENV_VARS,
    interactive_guest_disk_path,
    interactive_guest_enabled,
)

ROOT = Path(__file__).resolve().parents[2]


def test_interactive_guest_labels_honest():
    assert DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST is True
    assert SHIPPING_IMAGE is False
    # Slim guest label is untouched by adding the interactive guest.
    assert DEVICE_LAB_DEVELOPMENT_GUEST is True


def test_interactive_manifest_schema_and_required_packages():
    manifest = interactive_manifest(ROOT)
    assert manifest["schema"] == INTERACTIVE_GUEST_SCHEMA
    assert manifest["DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST"] is True
    assert manifest["SHIPPING_IMAGE"] is False
    assert manifest["SILICON_EXACT_EMULATION"] is False
    assert manifest["production_keys_used"] is False
    assert manifest["physical_boot_claimed"] is False
    # No PASS token or master-complete token is claimed by the manifest.
    assert manifest["pass_tokens_earned_by_this_manifest"] == []
    for forbidden in (
        "LIVE_GUNNCHOS_VISUAL_PASS",
        "DSXL_DUAL_COMPOSITOR_UX_PASS",
        "RING_TO_REAL_APP_STATE_MUTATION_PASS",
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
        "ECO010_SOAK_PASS",
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE",
    ):
        assert manifest.get(forbidden) is not True

    names = {p["name"] for p in REQUIRED_PACKAGES}
    assert {"weston", "seatd", "mesa-dri-gallium", "chromium", "nano", "pipewire", "libinput"} <= names
    godot = next(p for p in REQUIRED_PACKAGES if p["name"] == "godot")
    assert godot["optional"] is True
    weston = next(p for p in REQUIRED_PACKAGES if p["name"] == "weston")
    assert weston["optional"] is False


def test_arch_matrix_aarch64_and_x86_64():
    assert "aarch64" in ARCH_MATRIX and "x86_64" in ARCH_MATRIX
    assert ARCH_MATRIX["aarch64"]["implemented"] is True
    assert ARCH_MATRIX["aarch64"]["build_script"]
    build_script = ROOT / ARCH_MATRIX["aarch64"]["build_script"]
    assert build_script.is_file()
    assert os.access(build_script, os.X_OK)
    # x86_64 is honestly not yet implemented — no fake build script claimed.
    assert ARCH_MATRIX["x86_64"]["implemented"] is False
    assert ARCH_MATRIX["x86_64"]["build_script"] is None


def test_write_interactive_manifest_roundtrip(tmp_path: Path):
    builder = InteractiveGuestImageBuilder(tmp_path)
    path = builder.write_manifest()
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == INTERACTIVE_GUEST_SCHEMA
    assert data["DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST"] is True
    assert data["SHIPPING_IMAGE"] is False


def test_create_disk_placeholder_never_claims_formatted(tmp_path: Path):
    builder = InteractiveGuestImageBuilder(tmp_path)
    result = builder.create_disk_placeholder(arch="aarch64", size_gb=1)
    if not result.get("ok"):
        # Honest skip only when qemu-img is genuinely absent — never a fake pass.
        assert result.get("error") == "qemu-img_not_found"
        pytest.skip("qemu-img not available on this host")
    assert result["disk_formatted"] is False
    disk_path = Path(result["path"])
    assert disk_path.is_file()
    assert disk_path.suffix == ".qcow2"


def test_run_rootfs_build_x86_64_honestly_not_implemented(tmp_path: Path):
    builder = InteractiveGuestImageBuilder(tmp_path)
    result = builder.run_rootfs_build(arch="x86_64")
    assert result["ok"] is False
    assert result["error"] == "arch_build_script_not_implemented"


def test_detect_build_capability_structure():
    cap = detect_build_capability()
    assert cap["method"] in {"docker", "chroot_binfmt", "none"}
    assert "docker" in cap and "chroot_binfmt" in cap
    # ok must match method — never claim ok=True with method='none'.
    assert cap["ok"] == (cap["method"] != "none")


def test_guest_agent_supported_commands_include_interactive_additions():
    for cmd in ("framebuffer_capture", "compositor_info", "app_launch"):
        assert cmd in SUPPORTED_COMMANDS


def test_guest_agent_mailbox_stub_honest_for_interactive_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GUNNCH_GUEST_AGENT_MAILBOX", "1")
    monkeypatch.setenv("GUNNCH_GUEST_AGENT_HOST_STUB", "1")
    mailbox = tmp_path / "agent.mailbox"
    client = GuestAgentClient(mailbox, timeout_sec=2.0)

    fb = client.call("framebuffer_capture", path=str(tmp_path / "fake.ppm"))
    assert fb.get("ok") is False
    assert fb.get("stub") is True
    assert not (tmp_path / "fake.ppm").exists()

    comp = client.call("compositor_info")
    assert comp.get("stub") is True
    assert comp.get("available") is False
    assert comp.get("compositor") is None

    launch = client.call("app_launch", app="chromium")
    assert launch.get("ok") is False
    assert launch.get("stub") is True
    assert launch.get("started") is False


def test_qemu_interactive_guest_env_flag_recognition(monkeypatch: pytest.MonkeyPatch):
    for name in INTERACTIVE_GUEST_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    assert interactive_guest_enabled() is False
    monkeypatch.setenv(INTERACTIVE_GUEST_ENV_VARS[0], "1")
    assert interactive_guest_enabled() is True


def test_qemu_interactive_guest_disk_path(tmp_path: Path):
    path = interactive_guest_disk_path(tmp_path, arch="aarch64")
    assert path == tmp_path / "os_build" / "device_lab_interactive_guest" / "artifacts" / "interactive-root-aarch64.qcow2"


def test_gap_register_references_interactive_guest_as_required_path():
    gaps = json.loads((ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json").read_text())
    assert gaps["claim_firewall"]["DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST"]
    assert gaps["claim_firewall"]["SHIPPING_IMAGE"] is False
    required = gaps["required_guest_for_in_guest_proofs"]
    assert required["scaffolding_earns_no_pass_token"] is True
    for gap in gaps["gaps"]:
        if gap["token"] in {
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
            "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS",
        }:
            assert "interactive_guest" in gap["required_path"]
            # WP-011R.2: earned may be true when evidence is present; scaffolding alone still earns nothing.
            assert isinstance(gap["earned"], bool)
            if gap["earned"]:
                assert Path(ROOT / gap["evidence"]).is_file()
    # FOUR_GAME remains false until owner real builds replace probe/lab_bridge facades.
    assert gaps["pass_tokens"]["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] is False
    assert gaps["master_complete"] is False
    assert gaps["claim_firewall"]["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
