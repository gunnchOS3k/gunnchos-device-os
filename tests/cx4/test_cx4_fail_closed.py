"""Fail-closed CX4 tests — readiness ≠ PASS."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from gunnchos_device_os.cx4.blockers import build_blocker_register, write_edmund_action_packet
from gunnchos_device_os.cx4.canonical import validate_backing_chain
from gunnchos_device_os.cx4.evidence import pick_next_gate
from gunnchos_device_os.cx4.readiness import materialize_all_packets
from gunnchos_device_os.cx4.tokens import Cx4Tokens

ROOT = Path(__file__).resolve().parents[2]


def test_readiness_packet_cannot_equal_real_world_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.readiness_docs_root", lambda repo=None: tmp_path / "docs"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.ensure_lab_tree", lambda repo=None: tmp_path / "lab"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.evidence_root", lambda repo=None: tmp_path / "ev"
    )
    (tmp_path / "lab" / "harnesses").mkdir(parents=True)
    out = materialize_all_packets(ROOT)
    assert out["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert out["human_a11y"]["human_a11y_pass"] is False
    assert out["printer"]["PHYSICAL_PRINTER_PENDING"] is True
    assert out["printer"]["physical_printer_pass"] is False
    assert out["device_quartet"]["EVT_PENDING"] is True
    assert out["cert_mfg"]["certified"] is False
    assert out["privacy_rights"]["legal_approval"] is False
    assert out["chat_meeting"]["external_provider_integration_pass"] is False


def test_simulation_cannot_equal_physical_pass(tmp_path):
    path = ROOT / "os_build" / "cx4_linux_lab" / "harnesses" / "firmware_lifecycle_sim.py"
    spec = importlib.util.spec_from_file_location("fwsim", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    payload = mod.run(tmp_path)
    assert payload["physical_pass"] is False
    assert payload["failed_update_recovery"]["simulated"] is True


def test_automated_a11y_cannot_equal_human_a11y():
    t = Cx4Tokens(CX4_HUMAN_A11Y_PACKET_READY=True)
    assert t.J6_CLASS == "HUMAN_VALIDATION_PENDING"
    assert t.human_a11y_pass is False


def test_cups_digital_cannot_equal_physical_printer():
    t = Cx4Tokens(CX4_PHYSICAL_PRINTER_PACKET_READY=True)
    assert t.PHYSICAL_PRINTER_PENDING is True
    assert t.physical_printer_pass is False


def test_device_enum_fixture_cannot_equal_camera_mic_pass():
    t = Cx4Tokens(CX4_CAMERA_MIC_AV_PACKET_READY=True)
    assert t.PHYSICAL_CAMERA_MIC_AV_PENDING is True
    assert t.physical_camera_mic_av_pass is False


def test_evt_dvt_pvt_docs_cannot_set_pass_true():
    t = Cx4Tokens(CX4_EVT_PACKET_READY=True, CX4_DVT_PACKET_READY=True, CX4_PVT_PACKET_READY=True)
    assert t.EVT_PENDING and t.DVT_PENDING and t.PVT_PENDING
    assert not (t.evt_pass or t.dvt_pass or t.pvt_pass)


def test_certification_matrix_cannot_set_certified_true(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.readiness_docs_root", lambda repo=None: tmp_path / "docs"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.ensure_lab_tree", lambda repo=None: tmp_path / "lab"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.evidence_root", lambda repo=None: tmp_path / "ev"
    )
    (tmp_path / "lab" / "harnesses").mkdir(parents=True)
    materialize_all_packets(ROOT)
    matrix = json.loads((tmp_path / "docs" / "CERTIFICATION_MATRIX.json").read_text())
    assert matrix["certified"] is False


def test_legal_checklist_cannot_claim_legal_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.readiness_docs_root", lambda repo=None: tmp_path / "docs"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.ensure_lab_tree", lambda repo=None: tmp_path / "lab"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.evidence_root", lambda repo=None: tmp_path / "ev"
    )
    (tmp_path / "lab" / "harnesses").mkdir(parents=True)
    materialize_all_packets(ROOT)
    privacy = json.loads((tmp_path / "docs" / "PRIVACY_REVIEW_REGISTER.json").read_text())
    assert privacy["legal_approval"] is False


def test_manufacturing_packet_cannot_claim_pvt_or_mfg_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.readiness_docs_root", lambda repo=None: tmp_path / "docs"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.ensure_lab_tree", lambda repo=None: tmp_path / "lab"
    )
    monkeypatch.setattr(
        "gunnchos_device_os.cx4.readiness.evidence_root", lambda repo=None: tmp_path / "ev"
    )
    (tmp_path / "lab" / "harnesses").mkdir(parents=True)
    materialize_all_packets(ROOT)
    mfg = json.loads((tmp_path / "docs" / "MANUFACTURING_PACKET.json").read_text())
    assert mfg["manufacturing_pass"] is False
    assert mfg["pvt_pass"] is False


def test_external_provider_contract_cannot_claim_integration():
    t = Cx4Tokens(CX4_CHAT_MEETING_PROVIDER_READINESS_PASS=True)
    assert t.external_provider_integration_pass is False


def test_owner_action_packet_only_non_automatable(tmp_path):
    edmund = write_edmund_action_packet(tmp_path)
    text = Path(edmund["path"]).read_text()
    assert "Only non-automatable" in text
    assert edmund["automatable_actions_included"] is False
    reg = build_blocker_register()
    for b in reg["blockers"]:
        assert b["automatable_prework_complete"] is True


def test_guest_overlay_preflight_fails_on_missing_backing(tmp_path):
    missing = tmp_path / "missing.qcow2"
    result = validate_backing_chain(missing)
    assert result["ok"] is False
    assert result["blocker"] in {"CX4_OVERLAY_MISSING", "CX4_QEMU_IMG_MISSING", "CX4_BACKING_CHAIN_BROKEN"}


def test_readiness_complete_requires_pending_gates():
    t = Cx4Tokens(
        CX4_CURRENT_TIP_GUEST_OVERLAY_PASS=True,
        CX4_CURRENT_TIP_GUEST_SMOKE_PASS=True,
        CX4_HUMAN_A11Y_PACKET_READY=True,
        CX4_PHYSICAL_PRINTER_PACKET_READY=True,
        CX4_CAMERA_MIC_AV_PACKET_READY=True,
        CX4_PHYSICAL_PERIPHERAL_PACKET_READY=True,
        CX4_EVT_PACKET_READY=True,
        CX4_DVT_PACKET_READY=True,
        CX4_PVT_PACKET_READY=True,
        CX4_FIRMWARE_LIFECYCLE_PACKET_READY=True,
        CX4_SUPPORT_BUNDLE_READY=True,
        CX4_REPAIR_RMA_PACKET_READY=True,
        CX4_CHAT_MEETING_PROVIDER_READINESS_PASS=True,
        CX4_EXTERNAL_ISSUER_PACKET_READY=True,
        CX4_PRIVACY_REVIEW_PACKET_READY=True,
        CX4_RIGHTS_REGISTER_READY=True,
        CX4_CERTIFICATION_MATRIX_READY=True,
        CX4_MANUFACTURING_PACKET_READY=True,
        CX4_OWNER_ACTION_PACKET_READY=True,
    )
    assert t.readiness_complete() is True
    t.human_a11y_pass = True
    assert t.readiness_complete() is False
    assert pick_next_gate(Cx4Tokens()).startswith("CX4_0B_")
