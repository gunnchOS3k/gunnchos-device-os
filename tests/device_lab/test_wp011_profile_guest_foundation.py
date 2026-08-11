"""WP-011: profile sync, image manifests, QEMU start/stop honesty."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab import (
    GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE,
    GUNNCHDEVICE_LAB_GUEST_AGENT_PREPARED,
    GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED,
    GUNNCHDEVICE_LAB_PROFILE_SYNC_PREPARED,
    SILICON_EXACT_EMULATION,
)
from gunnchos_device_os.device_lab.guest_agent import GuestAgentClient
from gunnchos_device_os.device_lab.hardware_truth import load_accepted_hardware_truth
from gunnchos_device_os.device_lab.image_builder import LabGuestImageBuilder
from gunnchos_device_os.device_lab.profile_sync import diff_profiles, sync_profiles, verify_profiles
from gunnchos_device_os.device_lab.profiles import CATALOG, load_profile
from gunnchos_device_os.device_lab.virtualization.display_transport import scaffold_display_transport
from gunnchos_device_os.device_lab.virtualization.qemu_guest import environment_can_run_qemu, start_qemu_guest
from gunnchos_device_os.device_lab.session import register_lab_work_root, start_session, stop_session, unregister_lab_work_root


ROOT = Path(__file__).resolve().parents[2]


def test_master_completion_token_false():
    assert GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE is False
    assert SILICON_EXACT_EMULATION is False
    assert GUNNCHDEVICE_LAB_PROFILE_SYNC_PREPARED is True
    assert GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED is True
    assert GUNNCHDEVICE_LAB_GUEST_AGENT_PREPARED is True


def test_catalog_includes_dock():
    assert "dock" in CATALOG
    assert set(CATALOG) >= {
        "student_14_5",
        "dsxl_coder",
        "handheld_hybrid",
        "handheld_docked",
        "edge_io_rings",
        "full_ecosystem",
        "dock",
    }


def test_profile_sync_verify_clean():
    result = verify_profiles()
    assert result["ok"] is True
    assert result["gate"] == "PASS"
    assert result["SILICON_EXACT_EMULATION"] is False
    assert result["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False


def test_profile_mpn_ram_storage_from_hardware_truth():
    truth = load_accepted_hardware_truth()
    student = load_profile("student_14_5")
    assert student["ram"]["gb"] == 32
    assert student["compute"]["mpn"] == "COM-HPC-mMTL-155H-32G"
    assert student["storage"]["min_gb"] == 512
    assert student["storage"]["mpn"] == "PC801 512GB"
    handheld = load_profile("handheld_hybrid")
    assert handheld["ram"]["gb"] == 8
    assert handheld["compute"]["mpn"] == "RM121-D8E32"
    assert handheld["storage"]["min_gb"] == 32
    assert handheld["storage"]["class"] == "emmc"
    dsxl = load_profile("dsxl_coder")
    assert dsxl["ram"]["gb"] == 32
    assert len(dsxl["display_outputs"]) >= 2
    dock = load_profile("dock")
    assert dock["compute"]["mpn"] == "JHL8440"
    assert dock["exact_mpns"]["retimer"] == "JHL9040R"
    # Truth pin present
    assert student["hardware_truth_pin"]["hardware_repo_sha"] == truth["hardware_repo"]["pinned_sha"]


def test_profile_drift_gate_detects_stale_ram(tmp_path: Path):
    # Copy profiles then corrupt RAM
    for pid in CATALOG:
        src = ROOT / "gunnchos_device_os" / "device_lab" / "profiles" / f"{pid}.json"
        dst = tmp_path / f"{pid}.json"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    bad = json.loads((tmp_path / "student_14_5.json").read_text(encoding="utf-8"))
    bad["ram"] = {"gb": 8, "source": "stale"}
    (tmp_path / "student_14_5.json").write_text(json.dumps(bad, indent=2) + "\n", encoding="utf-8")
    result = verify_profiles(profiles_dir=tmp_path)
    assert result["ok"] is False
    assert result["gate"] == "FAIL_STALE_RAM_STORAGE_OR_MPN"
    assert any(f.get("profile_id") == "student_14_5" for f in result["failures"])


def test_profile_diff_and_sync_roundtrip(tmp_path: Path):
    sync_profiles(profiles_dir=tmp_path, write=True)
    d = diff_profiles(profiles_dir=tmp_path)
    assert d["ok"] is True
    assert all(v["status"] == "match" for v in d["diffs"].values())


def test_fidelity_modeled_not_physical_and_dsxl_dual():
    from gunnchos_device_os.device_lab.fidelity import FidelityDashboard, FidelityLevel, HonestyStatus, SubsystemFidelity
    from gunnchos_device_os.device_lab.hw_backends.display import DisplayBackend

    d = FidelityDashboard()
    d.cpu = SubsystemFidelity(
        "CPU_PERFORMANCE",
        FidelityLevel.VF3_MODELED,
        HonestyStatus.MODELED,
        notes="PHYSICAL_MEASURED",
    )
    assert d.assert_honest(), "modeled labeled physical must fail honesty"
    backend = DisplayBackend()
    backend.outputs = [{"id": "only", "role": "primary", "connected": True}]
    assert (backend.connected_count() >= 2) is False


def test_guest_agent_mailbox_ready(tmp_path: Path):
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "1"
    client = GuestAgentClient(tmp_path / "agent.mailbox", timeout_sec=2.0)
    ready = client.wait_ready(timeout_sec=2.0)
    assert ready["ok"] is True
    assert ready["ready"] is True
    metrics = client.call("metrics")
    assert metrics["ok"] is True
    assert metrics["SILICON_EXACT_EMULATION"] is False
    assert metrics.get("production_keys") is False


def test_display_transport_not_fake_screenshot():
    vnc = scaffold_display_transport(kind="vnc", display=7)
    assert vnc["fake_screenshot_only"] is False
    assert vnc["kind"] == "vnc"
    assert "5907" in vnc["listen"]


def test_image_inspect_or_verify_hashes():
    builder = LabGuestImageBuilder(ROOT)
    info = builder.inspect()
    # Either Lab manifest or bootable_reference artifacts may exist in-repo
    if info.get("ok"):
        verify = builder.verify()
        assert verify["SILICON_EXACT_EMULATION"] is False
        assert verify.get("GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE") is False
    else:
        pytest.skip("guest/reference artifacts not present in this checkout")


def test_qemu_start_stop_or_skipped_environment(tmp_path: Path):
    register_lab_work_root(tmp_path, repo_root=ROOT)
    # Clear forced TCG from prior tests so Mac HVF can run; CI sets ACCEL via job env.
    prior_accel = os.environ.pop("GUNNCHDEVICE_LAB_ACCEL", None)
    try:
        env = environment_can_run_qemu(repo_root=ROOT)
        profile = load_profile("handheld_hybrid")
        # Cap boot wait for CI/local
        os.environ["GUNNCHDEVICE_LAB_BOOT_TIMEOUT"] = "90"
        os.environ["GUNNCHDEVICE_LAB_MEMORY_MB"] = "512"
        os.environ.setdefault("GUNNCHDEVICE_LAB_QEMU_ARCH", "aarch64")
        result = start_qemu_guest(
            work=tmp_path / "qemu",
            profile=profile,
            repo_root=ROOT,
            headless=True,
        )
        if result.get("SKIPPED_ENVIRONMENT"):
            assert result.get("result") == "SKIPPED_ENVIRONMENT" or result.get("ok") is False
            # Must NOT be labeled PASS
            assert result.get("result") != "PASS"
            return
        sess = result.pop("_session", None)
        try:
            assert result.get("ok") is True
            assert result.get("qemu_alive") is True
            assert result["state"]["SILICON_EXACT_EMULATION"] is False
            # Guest agent readiness OR boot markers (HOST_OBSERVED)
            ga = result["state"].get("guest_agent") or {}
            assert ga.get("ready") or ga.get("boot_complete_observed") or result.get("boot_complete")
        finally:
            if sess is not None:
                stop = sess.stop()
                assert stop.get("ok") is True
    finally:
        unregister_lab_work_root(tmp_path)
        if prior_accel is not None:
            os.environ["GUNNCHDEVICE_LAB_ACCEL"] = prior_accel


def test_start_session_real_guest_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    register_lab_work_root(tmp_path, repo_root=ROOT)
    monkeypatch.setenv("GUNNCHDEVICE_LAB_FORCE_REAL_GUEST", "1")
    monkeypatch.setenv("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "90")
    monkeypatch.setenv("GUNNCHDEVICE_LAB_MEMORY_MB", "512")
    monkeypatch.setenv("GUNNCHDEVICE_LAB_QEMU_ARCH", "aarch64")
    try:
        # Point instances under approved tmp by monkeypatching via work=
        from gunnchos_device_os.device_lab import session as session_mod

        started = session_mod.start_session(
            "student_14_5",
            repo_root=ROOT,
            work=tmp_path / "dev-session",
        )
        inst = started["instance_id"]
        try:
            if started.get("SKIPPED_ENVIRONMENT"):
                assert started.get("ok") is False
                assert started.get("result") == "SKIPPED_ENVIRONMENT"
            else:
                qemu = (started.get("state") or {}).get("qemu") or {}
                # Real guest path engaged — PASS only if alive; else honest FAIL (not PASS)
                if qemu.get("ok"):
                    assert qemu.get("qemu_alive") is True
                else:
                    assert qemu.get("result") != "PASS"
                    assert qemu.get("ok") is False or qemu.get("SKIPPED_ENVIRONMENT") is True or qemu.get("error")
        finally:
            if inst in session_mod._INSTANCES:
                stop_session(inst)
    finally:
        unregister_lab_work_root(tmp_path)
