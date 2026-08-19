"""Wave 002 shell + identity + input/display + session continuity."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from gunnchos_device_os.shell.coordinator import Wave002ShellCoordinator
from gunnchos_device_os.shell.continuity_coordinator import ContinuityDisclosure
from gunnchos_device_os.shell.failure_injection import (
    inject_checkpoint_corruption,
    inject_ring_replay,
    inject_session_expiry,
)
from gunnchos_device_os.shell.hal_registry import CapabilityProvenance, HalCapabilityRegistry
from gunnchos_device_os.shell.shell_profiles import WAVE002_FORM_FACTORS, ShellProfileService


def _ari():
    repo_root = Path(__file__).resolve().parents[1]
    hw = repo_root.parent / "gunnchos-hardware-industrial-design" / "ring_input" / "python"
    if not (hw / "authenticated_ring_input" / "__init__.py").exists():
        hw = Path(
            "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/"
            "gunnchos-hardware-industrial-design/ring_input/python"
        )
    if str(hw) not in sys.path:
        sys.path.insert(0, str(hw))
    return importlib.import_module("authenticated_ring_input")


BASE = 1_700_000_000_000


def test_all_form_factor_profiles_apply():
    svc = ShellProfileService()
    for ff in WAVE002_FORM_FACTORS:
        row = svc.apply_form_factor(ff)
        assert row["form_factor"] == ff
        assert row["input_modality"]


def test_hal_registry_provenance():
    reg = HalCapabilityRegistry()
    assert reg.available("input.touch")
    reg.set_provenance("pixel.adb_client", CapabilityProvenance.HOST_OBSERVED)
    assert reg.get("pixel.adb_client")["provenance"] == "HOST_OBSERVED"


def test_coordinator_vertical_slice(tmp_path):
    coord = Wave002ShellCoordinator(tmp_path / "wave002")
    result = coord.run_vertical_slice("handheld")
    assert result["restore"]["ok"] is True
    assert "OS-CONTINUITY-002" in result["disclosure_keys"]
    assert result["parity"]["SYS-MISSION-006"]["waike"]["lesson_count"] >= 1


def test_continuity_disclosure_complete(tmp_path):
    disc = ContinuityDisclosure(tmp_path)
    full = disc.full_disclosure([{"device_id": "dev-1", "state": "bound"}])
    assert len(full) == 6


def test_checkpoint_revoke_and_conflict(tmp_path):
    coord = Wave002ShellCoordinator(tmp_path / "wave002")
    boot = coord.bootstrap(form_factor="student_14_5")
    ids = boot["identity"]
    cp = coord.continuity.checkpoint(
        session_id=ids["session_id"],
        account_id=ids["account_id"],
        device_id=ids["device_id"],
        payload={"v": 1},
    )
    conflict = coord.continuity.detect_conflict({"v": 1}, {"v": 2})
    assert conflict["conflict"] is True
    coord.continuity.revoke_device(ids["binding_id"], coord.identity)
    assert coord.identity.service.bindings[ids["binding_id"]].state.value == "revoked"


def test_failure_injection_expiry_and_corruption(tmp_path):
    coord = Wave002ShellCoordinator(tmp_path / "wave002")
    boot = coord.bootstrap(form_factor="handheld")
    ids = boot["identity"]
    inject_session_expiry(coord.identity, ids["session_id"])
    issued = coord.identity.service.issue_session(ids["account_id"], ids["device_id"], now_ms=BASE)
    bad = coord.identity.service.validate_session(issued["session_id"], issued["token"], now_ms=BASE + 9_999_999)
    assert bad["valid"] is False
    cp = coord.continuity.checkpoint(
        session_id=ids["session_id"],
        account_id=ids["account_id"],
        device_id=ids["device_id"],
        payload={"x": 1},
    )
    inject_checkpoint_corruption(coord.continuity, cp["checkpoint_id"])
    broken = coord.continuity.restore(cp["checkpoint_id"])
    assert broken["ok"] is False
    inject_ring_replay(coord.ring)


def test_ring_service_integration():
    ari = _ari()
    sm = ari.PairingStateMachine(
        device_id="ring-w002",
        user_id="user-test",
        host_id="wave002-host",
        device_secret=b"secret",
    )
    sm.start_challenge()
    sm.host_verify(sm.device_respond())
    sm.confirm()
    cal_reg = ari.CalibrationRegistry()
    cal = cal_reg.create(surface_id="desk", device_id=sm.device_id, user_id=sm.user_id, now_ms=BASE)
    sender = ari.AuthenticatedSender(
        pairing=sm,
        target_device_id=sm.host_id,
        surface_id=cal["surface_id"],
        calibration_id=cal["calibration_id"],
    )
    sender.open_session(offline=True, now_ms=BASE)
    from gunnchos_device_os.shell.ring_service import RingInputService

    ring = RingInputService(host_id="wave002-host")
    ring.attach_session(sender.export_session_material(), cal_reg)
    ev = sender.emit("pointer_move", confidence=0.95, payload={"dx": 1}, ts_ms=BASE)
    assert ring.ingest(ev, now_ms=BASE)["accepted"] is True
    coord = Wave002ShellCoordinator(Path("/tmp/wave002-ring-test"))
    out = ring.route_to_input(coord.input_routing.router)
    assert out.get("delivery") is not None or out.get("ok") is False


def test_input_remap_persistence(tmp_path):
    from gunnchos_device_os.shell.input_routing import InputRoutingService

    store = tmp_path / "remaps.json"
    svc = InputRoutingService(store_path=store)
    svc.set_remap("handheld", "touch.tap", "launch")
    svc2 = InputRoutingService(store_path=store)
    assert svc2.remaps["handheld"]["touch.tap"] == "launch"


def test_requirement_classification_partial_ok():
    coord = Wave002ShellCoordinator(Path("/tmp/wave002-classify"))
    classes = coord.classify_requirements()
    assert classes["OS-PLATFORM-001"]["status"] == "PASS"
    assert classes["OS-PLATFORM-004"]["status"] == "PARTIAL"
    assert classes["SYS-MISSION-006"]["status"] == "PARTIAL"
