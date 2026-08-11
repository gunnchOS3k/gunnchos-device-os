"""WP-011 Wave 3: virtio-serial agent path, dual-output honesty, ring OS input."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import (
    GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE,
    SILICON_EXACT_EMULATION,
)
from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient
from gunnchos_device_os.device_lab.hw_backends.rings import RingsBackend
from gunnchos_device_os.device_lab.session import register_lab_work_root, unregister_lab_work_root
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import high_fidelity_dual_gate
from gunnchos_device_os.device_lab.virtualization.qemu_guest import (
    environment_can_run_qemu,
    lab_guest_image_arch,
    qemu_system_bin,
    start_qemu_guest,
)
from gunnchos_device_os.device_lab.profiles import load_profile


ROOT = Path(__file__).resolve().parents[2]


def test_claim_firewall_master_still_false():
    assert GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE is False
    assert SILICON_EXACT_EMULATION is False
    tokens = json.loads((ROOT / "gunnchos_device_os/device_lab/TOKENS_WP011.json").read_text(encoding="utf-8"))
    assert tokens["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert tokens["SILICON_EXACT_EMULATION"] is False
    assert tokens["GUEST_DUAL_OUTPUT_PASS"] is False
    # Default token remains false until earned in a live run; register may flip after proof only.
    assert tokens["RING_TO_REAL_APPLICATION_INPUT_PASS"] is False


def test_qemu_prefers_guest_image_arch_not_host_x86():
    """CI x86 must not select qemu-system-x86_64 against aarch64 Lab guest."""
    arch = lab_guest_image_arch(ROOT)
    assert arch == "aarch64"
    env = os.environ.pop("GUNNCHDEVICE_LAB_QEMU_ARCH", None)
    try:
        _bin, selected = qemu_system_bin(repo_root=ROOT)
        assert selected == "aarch64"
        assert "aarch64" in _bin
    finally:
        if env is not None:
            os.environ["GUNNCHDEVICE_LAB_QEMU_ARCH"] = env


def test_device_attached_virtio_gpu_is_not_guest_dual_pass():
    attached = [
        {
            "id": "guest-gpu0-out0",
            "connected": False,
            "source": "qemu_virtio_gpu_device_attached",
            "class": "host_device_intent",
        },
        {
            "id": "guest-gpu0-out1",
            "connected": False,
            "source": "qemu_virtio_gpu_device_attached",
            "class": "host_device_intent",
        },
    ]
    gate = high_fidelity_dual_gate(attached, claim_guest_dual=False)
    assert gate["GUEST_DUAL_OUTPUT_PASS"] is False

    # Claiming guest dual from device-attach-only must fail
    fake_claim = [
        {**attached[0], "connected": True, "source": "profile_logical"},
        {**attached[1], "connected": True, "source": "profile_logical"},
    ]
    bad = high_fidelity_dual_gate(fake_claim, claim_guest_dual=True)
    assert bad["ok"] is False
    assert bad["GUEST_DUAL_OUTPUT_PASS"] is False


def test_ring_fallback_mutates_browser_and_os_input_path_wired(tmp_path: Path):
    register_lab_work_root(tmp_path, repo_root=ROOT)
    try:
        rings = RingsBackend()
        info = rings.start(evidence_dir=tmp_path / "ring", repo_root=ROOT)
        assert "input_router_hid_wayland" in info["pipeline"]
        rings.guest_process = rings.surfaces.browser
        delivered = rings.inject(target="browser", confidence=0.95, gesture="click")
        assert delivered["delivered"] is True
        assert delivered["app_state_changed"] is True
        os_path = delivered.get("os_input_path") or {}
        assert os_path.get("attempted") is True
        assert os_path.get("RING_SPATIAL_ACCURACY") == "SIMULATED"
        # Without live guest agent, PASS must stay false
        assert os_path.get("RING_TO_REAL_APPLICATION_INPUT_PASS") is False
        fb = rings.fallback_conventional()
        assert fb.get("ok") is True
    finally:
        unregister_lab_work_root(tmp_path)


def test_mailbox_stub_labeled_not_virtio():
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "1"
    client = GuestAgentClient(Path("/tmp/wave3-agent.mailbox"), timeout_sec=2.0)
    ping = client.ping()
    assert ping.get("transport") == "host_mailbox_stub"
    assert ping.get("agent_path_label") == "host_mailbox_stub"
    assert ping.get("stub") is not False or "stub" not in ping


def test_agent_path_or_honest_partial_on_qemu(tmp_path: Path):
    """Prove virtio-serial agent_path_label when possible; else honest FAIL/PARTIAL."""
    register_lab_work_root(tmp_path, repo_root=ROOT)
    env = environment_can_run_qemu(repo_root=ROOT)
    if not env.get("ok"):
        pytest.skip("QEMU absent")
    os.environ["GUNNCHDEVICE_LAB_BOOT_TIMEOUT"] = os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "90")
    os.environ["GUNNCHDEVICE_LAB_MEMORY_MB"] = "512"
    # Prefer host accel (HVF/KVM); only force TCG when explicitly requested (CI).
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ["GUNNCHDEVICE_LAB_QEMU_ARCH"] = "aarch64"
    profile = load_profile("handheld_hybrid")
    result = start_qemu_guest(
        work=tmp_path / "qemu-wave3",
        profile=profile,
        repo_root=ROOT,
        headless=True,
    )
    sess = result.pop("_session", None)
    try:
        if result.get("SKIPPED_ENVIRONMENT"):
            assert result.get("result") == "SKIPPED_ENVIRONMENT"
            assert result.get("ok") is False
            return
        if not result.get("ok"):
            # Honest FAIL — not PASS
            assert result.get("result") == "FAIL" or result.get("ok") is False
            assert result.get("result") != "PASS"
            return
        ga = (result.get("state") or {}).get("guest_agent") or {}
        label = ga.get("agent_path_label") or ga.get("transport") or ""
        # Accept virtio-serial primary, or explicitly labeled mailbox fallback / FAIL
        assert label in {
            "virtio-serial",
            "virtio_serial",
            "host_mailbox_stub_fallback",
            "host_mailbox_stub",
            "FAIL_NO_AGENT",
        } or "mailbox" in label or "virtio" in label
        if label in {"virtio-serial", "virtio_serial"}:
            # Real virtio path earned
            assert ga.get("transport") == "virtio_serial"
            # process_start via agent should not be stub when virtio
            agent = sess.agent if sess is not None else None
            if agent is not None:
                started = agent.call("process_start", name="lab-wave3")
                assert started.get("transport") == "virtio_serial"
                assert started.get("stub") is False
        else:
            # Honest partial — mailbox fallback labeled
            assert "mailbox" in label or label == "FAIL_NO_AGENT"
    finally:
        if sess is not None:
            sess.stop()
        unregister_lab_work_root(tmp_path)
        os.environ.pop("GUNNCHDEVICE_LAB_QEMU_ARCH", None)
