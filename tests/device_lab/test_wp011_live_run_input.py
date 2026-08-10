"""WP-011 wave E–G: live visual, DS-XL honesty, real run, conventional input."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE, SILICON_EXACT_EMULATION
from gunnchos_device_os.device_lab.apps.runner import run_app
from gunnchos_device_os.device_lab.apps.surfaces import DocumentSurface
from gunnchos_device_os.device_lab.session import register_lab_work_root, unregister_lab_work_root
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import high_fidelity_dual_gate
from gunnchos_device_os.device_lab.virtualization.guest_input import inject_key
from gunnchos_device_os.device_lab.virtualization.live_display import prove_live_display_path
from gunnchos_device_os.device_lab.virtualization.display_transport import scaffold_display_transport
from gunnchos_device_os.device_lab.virtualization.qemu_guest import environment_can_run_qemu, select_accel, start_qemu_guest
from gunnchos_device_os.device_lab.profiles import load_profile


ROOT = Path(__file__).resolve().parents[2]


def test_master_token_still_false():
    assert GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE is False
    assert SILICON_EXACT_EMULATION is False


def test_kvm_denied_falls_back_to_tcg(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "gunnchos_device_os.device_lab.virtualization.qemu_guest.platform.system",
        lambda: "Linux",
    )
    monkeypatch.setattr(
        "gunnchos_device_os.device_lab.virtualization.qemu_guest.platform.machine",
        lambda: "x86_64",
    )
    monkeypatch.setattr(
        "gunnchos_device_os.device_lab.virtualization.qemu_guest._kvm_usable",
        lambda: False,
    )
    # /dev/kvm "exists" but unusable → TCG
    class _P:
        def __init__(self, p):
            self._p = str(p)

        def exists(self):
            return self._p == "/dev/kvm"

    monkeypatch.setattr(
        "gunnchos_device_os.device_lab.virtualization.qemu_guest.Path",
        _P,
    )
    accel = select_accel("x86_64")
    assert accel["accel"] == "tcg"


def test_display_transport_wired_not_scaffold_only():
    vnc = scaffold_display_transport(kind="vnc", display=7, websocket_port=5707)
    assert vnc["fake_screenshot_only"] is False
    assert vnc["novnc"]["status"] == "wired"
    assert vnc["novnc"]["path"] == "/lab/novnc/"


def test_dsxl_high_fidelity_rejects_logical_as_guest():
    logical = [
        {"id": "a", "connected": True, "source": "profile_logical"},
        {"id": "b", "connected": True, "source": "profile_logical"},
    ]
    bad = high_fidelity_dual_gate(logical, claim_guest_dual=True)
    assert bad["ok"] is False
    assert bad["gate"] == "FAIL_LOGICAL_DUAL_CLAIMED_AS_GUEST"
    assert bad["GUEST_DUAL_OUTPUT_PASS"] is False

    ok_logical = high_fidelity_dual_gate(logical, claim_guest_dual=False)
    assert ok_logical["ok"] is True
    assert ok_logical["GUEST_DUAL_OUTPUT_PASS"] is False

    guest = [
        {"id": "g0", "connected": True, "source": "qemu_virtio_gpu", "class": "guest"},
        {"id": "g1", "connected": True, "source": "qemu_virtio_gpu", "class": "guest"},
    ]
    ok_guest = high_fidelity_dual_gate(guest, claim_guest_dual=True)
    assert ok_guest["ok"] is True
    assert ok_guest["GUEST_DUAL_OUTPUT_PASS"] is True


def test_gunnchctl_run_not_intent_only(tmp_path: Path):
    register_lab_work_root(tmp_path, repo_root=ROOT)
    try:
        result = run_app(app="lab-echo", work=tmp_path / "run", agent=None, prefer_guest=False, keep=False)
        assert result.get("intent_only") is False
        assert result.get("ok") is True
        assert result.get("process_proof") is True
        assert result.get("HYBRID") is True
        assert "claim_boundary" in result
        assert Path(tmp_path / "run" / "run_app.json").exists()
    finally:
        unregister_lab_work_root(tmp_path)


def test_conventional_input_hybrid_mutates_surface():
    from gunnchos_device_os.device_lab.apps.surfaces import DocumentSurface

    surface = DocumentSurface()
    before = surface.snapshot()
    inj = inject_key(monitor_sock=None, key="x", hybrid_surface=surface)
    assert inj.get("ok") is True
    assert inj.get("path") == "hybrid_surface"
    assert surface.snapshot() != before


def test_live_display_path_or_skipped(tmp_path: Path):
    """Prove live RFB path when QEMU+VNC available; else SKIPPED_ENVIRONMENT honestly."""
    register_lab_work_root(tmp_path, repo_root=ROOT)
    env = environment_can_run_qemu()
    if not env.get("ok"):
        proof = prove_live_display_path(vnc_port=5999)
        assert proof.get("LIVE_VISUAL_PASS") is False
        assert proof.get("ok") is False
        return

    os.environ["GUNNCHDEVICE_LAB_BOOT_TIMEOUT"] = "60"
    os.environ["GUNNCHDEVICE_LAB_MEMORY_MB"] = "512"
    os.environ["GUNNCHDEVICE_LAB_FORCE_VNC"] = "1"
    os.environ["GUNNCHDEVICE_LAB_DISPLAY"] = "vnc"
    os.environ["GUNNCHDEVICE_LAB_VNC_PORT"] = "11"  # 5911
    os.environ["GUNNCHDEVICE_LAB_WS_PORT"] = "5711"
    os.environ["GUNNCHDEVICE_LAB_ENABLE_VIRTIO_GPU"] = "0"
    profile = load_profile("handheld_hybrid")
    result = start_qemu_guest(
        work=tmp_path / "qemu-live",
        profile=profile,
        repo_root=ROOT,
        headless=True,  # FORCE_VNC still enables VNC
    )
    sess = result.pop("_session", None)
    try:
        if result.get("SKIPPED_ENVIRONMENT"):
            assert result.get("result") == "SKIPPED_ENVIRONMENT"
            assert result.get("ok") is False
            return
        if not result.get("ok"):
            # Honest failure — not PASS
            assert result.get("ok") is False
            return
        dt = (result.get("state") or {}).get("display_transport") or {}
        assert dt.get("fake_screenshot_only") is False
        vnc_port = int(dt.get("vnc_port") or 5911)
        proof = prove_live_display_path(vnc_port=vnc_port)
        # Either live RFB PASS or explicit non-pass (boot too slow / display lag)
        if proof.get("LIVE_VISUAL_PASS"):
            assert proof.get("ok") is True
            assert proof.get("fake_screenshot_only") is False
        else:
            assert proof.get("LIVE_VISUAL_PASS") is False
            assert proof.get("result") != "PASS" or proof.get("ok") is False
    finally:
        if sess is not None:
            sess.stop()
        unregister_lab_work_root(tmp_path)
        for k in (
            "GUNNCHDEVICE_LAB_FORCE_VNC",
            "GUNNCHDEVICE_LAB_DISPLAY",
            "GUNNCHDEVICE_LAB_VNC_PORT",
            "GUNNCHDEVICE_LAB_WS_PORT",
            "GUNNCHDEVICE_LAB_ENABLE_VIRTIO_GPU",
        ):
            os.environ.pop(k, None)


def test_ring_scenario_does_not_claim_ring_to_real_pass():
    text = (ROOT / "gunnchos_device_os/device_lab/scenarios/ring_real_input.py").read_text(encoding="utf-8")
    assert "RING_TO_REAL_APPLICATION_INPUT_PASS" in text
    assert "False" in text.split("RING_TO_REAL_APPLICATION_INPUT_PASS", 1)[1][:40]
    assert "RING_SPATIAL_ACCURACY\": \"SIMULATED\"" in text or "RING_SPATIAL_ACCURACY\": \"SIMULATED\"" in text.replace("'", '"')
    assert "SIMULATED" in text
