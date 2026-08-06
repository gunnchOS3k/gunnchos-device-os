"""Gate 1 Workstream C — dock continuity tests."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.dock.capabilities import load_capabilities
from gunnchos_device_os.dock.collector import collect_host_dock_signals
from gunnchos_device_os.dock.continuity import DockContinuityEngine
from gunnchos_device_os.dock.simulator import STATUS_PHYSICAL_PENDING, STATUS_SIM_PASS, run_dock_simulation
from gunnchos_device_os.dock.validator import run_dock_validation
from gunnchos_device_os.identity import sha256_json


def test_capability_descriptors_no_vendor_assumptions():
    caps = load_capabilities()
    policy = caps["detection_policy"]
    assert policy["never_assume_pixel"] is True
    assert policy["never_assume_usb_c_dp_alt_mode"] is True
    for dock in caps["dock_classes"]:
        assert dock["display"].get("assumes_dp_alt_mode") is False


def test_attach_detach_continuity():
    eng = DockContinuityEngine()
    eng.save_blob = {"slot": 1, "progress": 7}
    eng.apps = ["launcher", "game"]
    before_save = sha256_json(eng.save_blob)
    eng.attach("dock-A", external_display=True, ethernet=True, audio_dock=True)
    assert eng.docked is True
    assert eng.display_state["external"] is True
    assert eng.network_route == "ethernet-via-dock"
    assert eng.audio_route == "dock-audio"
    assert eng.power_state == "dock-power"
    snap = eng.snapshot_session()
    assert snap["save_checksum"] == before_save
    eng.safe_undock()
    assert eng.docked is False
    assert eng.apps == ["launcher", "game"]
    assert eng.identity["user"] == "local"
    assert sha256_json(eng.save_blob) == before_save
    assert eng.layout_profile == "handheld"


def test_degraded_and_interruption_recovery():
    eng = DockContinuityEngine()
    eng.save_blob = {"x": 1}
    eng.attach("dock-B")
    eng.enter_degraded_mode("link_loss")
    assert eng.degraded is True
    assert eng.layout_profile == "degraded-internal-only"
    eng.snapshot_session()
    eng.apps = ["junk"]
    ev = eng.recover_interruption()
    assert ev["ok"] is True
    assert eng.apps != ["junk"]


def test_simulation_pass_token():
    result = run_dock_simulation()
    assert result["continuity_ok"] is True
    assert STATUS_SIM_PASS in result["status_tokens"]
    assert STATUS_PHYSICAL_PENDING in result["status_tokens"]
    assert result["physical_dock"] is False


def test_validator_records_before_after(tmp_path):
    out = tmp_path / "dock.json"
    evidence = run_dock_validation(simulate=True, collect_host=True, out_path=out)
    assert out.exists()
    assert evidence["display_before"]["external"] is False
    assert evidence["display_after"]["external"] is True
    assert "save_checksum" in evidence
    assert "latencies_ms" in evidence
    assert STATUS_SIM_PASS in evidence["status_tokens"]
    assert STATUS_PHYSICAL_PENDING in evidence["status_tokens"]


def test_host_collector_no_assumptions():
    signals = collect_host_dock_signals()
    assert signals["assumes_pixel"] is False
    assert signals["assumes_usb_c_dp_alt_mode"] is False
    assert signals["observed"]["dp_alt_mode_proven"] is False
    assert STATUS_PHYSICAL_PENDING in signals["status_tokens"]


def test_cli_simulation(tmp_path):
    from gunnchos_device_os.dock.cli import main

    out = tmp_path / "dock_evidence.json"
    rc = main(["--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert STATUS_SIM_PASS in data["status_tokens"]
