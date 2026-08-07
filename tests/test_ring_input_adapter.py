"""Tests for gunnchOS ring input adapter."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from ring_input import PHYSICAL_RING_CLAIMED, STATUSES, RingInputAdapter


def _ari():
    repos_root = Path(__file__).resolve().parents[2]
    candidates = [
        repos_root / "gunnchos-hardware-industrial-design" / "ring_input" / "python",
        Path(__file__).resolve().parents[1].parent.parent
        / "gunnchos-hardware-industrial-design"
        / "ring_input"
        / "python",
        Path(
            "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/"
            "gunnchos-hardware-industrial-design/ring_input/python"
        ),
    ]
    # parents[1]=tests, parents[2]=device-os repo; sibling is alongside repo root
    repo_root = Path(__file__).resolve().parents[1]
    candidates.insert(
        0,
        repo_root.parent / "gunnchos-hardware-industrial-design" / "ring_input" / "python",
    )
    for root in candidates:
        if (root / "authenticated_ring_input" / "__init__.py").exists():
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            return importlib.import_module("authenticated_ring_input")
    raise ImportError(
        "authenticated_ring_input reference not found; expected sibling "
        "gunnchos-hardware-industrial-design/ring_input/python"
    )


BASE = 1_700_000_000_000


def _setup():
    ari = _ari()
    sm = ari.PairingStateMachine(
        device_id="ring-sim-001",
        user_id="user-alice",
        host_id="host-dsxl-01",
        device_secret=b"device-secret-software-only",
        permission_scope=[
            "pointer_move",
            "click",
            "key_press",
            "scroll",
            "heartbeat",
            "destructive_confirm",
        ],
    )
    sm.start_challenge()
    assert sm.host_verify(sm.device_respond())
    sm.confirm()
    cal_reg = ari.CalibrationRegistry()
    cal = cal_reg.create(
        surface_id="desk-surface-a",
        device_id=sm.device_id,
        user_id=sm.user_id,
        now_ms=BASE,
    )
    sender = ari.AuthenticatedSender(
        pairing=sm,
        target_device_id=sm.host_id,
        surface_id=cal["surface_id"],
        calibration_id=cal["calibration_id"],
    )
    sender.open_session(offline=True, now_ms=BASE)
    adapter = RingInputAdapter(host_id=sm.host_id)
    adapter.attach_session(sender.export_session_material(), cal_reg)
    return ari, sender, adapter


def test_valid_accept_maps_to_os_action():
    _, sender, adapter = _setup()
    ev = sender.emit("pointer_move", confidence=0.95, payload={"dx": 2}, ts_ms=BASE)
    action = adapter.ingest(ev, now_ms=BASE)
    assert action is not None
    assert action.authenticated
    assert action.kind == "pointer_delta"


def test_bad_signature_engages_fallback():
    _, sender, adapter = _setup()
    ev = sender.emit("click", confidence=0.95, ts_ms=BASE)
    ev["mac"] = "0" * 64
    assert adapter.ingest(ev, now_ms=BASE) is None
    assert adapter.fallback.active
    assert adapter.fallback.available()


def test_revoked_rejected():
    ari, sender, adapter = _setup()
    adapter.receiver.revocation.revoke_device("ring-sim-001")
    ev = sender.emit("click", confidence=0.95, ts_ms=BASE)
    assert adapter.ingest(ev, now_ms=BASE) is None


def test_low_confidence_destructive_rejected():
    _, sender, adapter = _setup()
    ev = sender.emit("destructive_confirm", confidence=0.3, ts_ms=BASE)
    assert adapter.ingest(ev, now_ms=BASE) is None
    assert adapter.fallback.active


def test_offline_paired_path():
    ari = _ari()
    sm = ari.PairingStateMachine(
        device_id="ring-sim-001",
        user_id="user-alice",
        host_id="host-dsxl-01",
        device_secret=b"secret",
    )
    sm.start_challenge()
    sm.host_verify(sm.device_respond())
    sm.confirm()
    assert sm.is_paired_offline()


def test_fallback_available_status():
    adapter = RingInputAdapter()
    assert adapter.fallback.available()
    st = adapter.status()
    assert st["physical_ring_claimed"] is False
    assert st["statuses"]["RING_PHYSICAL_PROTOTYPE_PENDING"] is True


def test_status_constants():
    assert STATUSES["AUTHENTICATED_INPUT_PROTOCOL_PASS"] is True
    assert PHYSICAL_RING_CLAIMED is False
