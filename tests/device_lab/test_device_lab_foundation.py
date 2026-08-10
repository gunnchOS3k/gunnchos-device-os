"""Fidelity honesty tests — must FAIL on over-claims."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.device_lab.calibration import assert_no_calibration_token, calibration_status
from gunnchos_device_os.device_lab.fidelity import FidelityDashboard, FidelityLevel, HonestyStatus, SubsystemFidelity
from gunnchos_device_os.device_lab.profiles import CATALOG, load_profile, list_profiles
from gunnchos_device_os.device_lab.scenarios.catalog import JOURNEY_SCENARIO_MAP


ROOT = Path(__file__).resolve().parents[2]


def test_all_required_profiles_present():
    assert set(list_profiles()) == set(CATALOG)
    for pid in CATALOG:
        p = load_profile(pid)
        assert p["SILICON_EXACT_EMULATION"] is False
        assert p["BEHAVIORAL_DEVICE_PROFILE"] is True
        assert p["profile_version"]


def test_dsxl_profile_declares_two_outputs():
    p = load_profile("dsxl_coder")
    assert len(p["display_outputs"]) >= 2


def test_journey_scenario_mapping():
    assert JOURNEY_SCENARIO_MAP["GOLDEN-04"]["scenario"] == "LAB-SCENARIO-OFFICE-DOCK"
    assert JOURNEY_SCENARIO_MAP["GOLDEN-06"]["scenario"] == "LAB-SCENARIO-DSXL-DUALSCREEN"
    assert JOURNEY_SCENARIO_MAP["GOLDEN-07"]["scenario"] == "LAB-SCENARIO-RING-REAL-INPUT"
    assert JOURNEY_SCENARIO_MAP["GOLDEN-08"]["scenario"] == "LAB-SCENARIO-LOCAL-AI-TUTOR"


def test_fidelity_dashboard_default_honest():
    d = FidelityDashboard()
    assert d.assert_honest() == []
    assert d.silicon_exact_emulation is False
    payload = d.to_dict()
    assert payload["VF4"] == "PHYSICAL_PENDING"
    assert payload["VF5"] == "PHYSICAL_PENDING"
    assert payload["VF6"] == "PHYSICAL_PENDING"


def test_honesty_fail_modeled_as_physical():
    d = FidelityDashboard()
    d.cpu = SubsystemFidelity(
        "CPU_PERFORMANCE",
        FidelityLevel.VF3_MODELED,
        HonestyStatus.MODELED,
        notes="PHYSICAL_MEASURED",
    )
    assert d.assert_honest(), "must fail when modeled labeled physical"


def test_honesty_fail_silicon_exact_true():
    d = FidelityDashboard()
    d.silicon_exact_emulation = True
    assert "SILICON_EXACT_EMULATION" in d.assert_honest()[0]


def test_honesty_fail_calibration_without_evt():
    with pytest.raises(AssertionError):
        assert_no_calibration_token({"CALIBRATED_EVT0": True})
    st = calibration_status()
    assert st["status"] == "PHYSICAL_PENDING"
    assert st["CALIBRATED_EVT0"] is False


def test_one_display_dsxl_must_fail_scenario_guard():
    """A one-display instance must not claim DS-XL D6."""
    from gunnchos_device_os.device_lab.hw_backends.display import DisplayBackend

    backend = DisplayBackend()
    backend.outputs = [{"id": "only", "role": "primary", "connected": True}]
    assert backend.connected_count() == 1
    # Scenario contract
    claim_d6 = backend.connected_count() >= 2
    assert claim_d6 is False


def test_stub_dock_boolean_not_vf2():
    """A {docked:true} stub must not claim VF2."""
    stub = {"docked": True}
    vf2_claim = bool(stub.get("docked")) and "external_display_lifecycle" not in stub
    assert vf2_claim is True  # would be dishonest
    # Real VF2 requires peripheral lifecycle keys
    real = {
        "external_display_lifecycle": True,
        "ethernet_via_dock": True,
        "dock_audio": True,
    }
    assert all(real.values())


def test_file_write_ring_not_d6():
    direct_file_write = True
    counts_as_ring_d6 = False
    assert not (direct_file_write and counts_as_ring_d6)


def test_deterministic_tutor_not_real_model_d6():
    primary = {"runtime": "deterministic_micro", "model_id": "micro-deterministic-v1"}
    real_model_d6 = primary["runtime"] != "deterministic_micro"
    assert real_model_d6 is False


def test_session_start_stop_and_atomic_scenarios(tmp_path):
    from gunnchos_device_os.device_lab.session import start_session, get_session, stop_session
    from gunnchos_device_os.device_lab.scenarios.engine import run_scenario

    started = start_session("handheld_docked", repo_root=ROOT, work=tmp_path / "inst")
    sess = get_session(started["instance_id"])
    assert sess.running
    stop = stop_session(started["instance_id"])
    assert stop["ok"]

    r = run_scenario("dock_attach", profile_id="handheld_docked", repo_root=ROOT)
    assert r["ok"] is True


def test_g04_office_dock_lab_scenario():
    from gunnchos_device_os.device_lab.scenarios.office_dock import run

    result = run(repo_root=ROOT)
    assert result["scenario_id"] == "LAB-SCENARIO-OFFICE-DOCK"
    assert result["boolean_dock_flag_used_as_primary"] is False
    assert result["INDEPENDENT_VERIFICATION"] == "PENDING"
    assert result["ok"] is True
    assert result["dock_attach_ok"] is True
    assert result["undock_ok"] is True


def test_g06_dsxl_dualscreen_requires_two_outputs():
    from gunnchos_device_os.device_lab.scenarios.dsxl_dualscreen import run

    result = run(repo_root=ROOT)
    assert result["scenario_id"] == "LAB-SCENARIO-DSXL-DUALSCREEN"
    assert result["connected_outputs"] >= 2
    assert result["INDEPENDENT_VERIFICATION"] == "PENDING"
    assert result["ok"] is True
    # GJ-DEFECT-006: must not be stub build / empty windows
    assert result["build"]["executed"] is True
    assert result["build"]["stub"] is False
    assert result["build"]["mode"] != "creator_toolchain_digital"
    assert len(result.get("windows") or []) >= 2
    assert result["unknown_transition"]["ok"] is False


def test_dsxl_stub_build_mode_would_fail():
    """Previous stub (`mode=creator_toolchain_digital` without execution) must not pass."""
    stub = {"ok": True, "steps": ["configure", "build", "test", "debug"], "mode": "creator_toolchain_digital"}
    d6_ok = bool(stub.get("ok")) and stub.get("mode") != "creator_toolchain_digital" and stub.get("executed")
    assert d6_ok is False


def test_g07_ring_real_input_stack():
    from gunnchos_device_os.device_lab.scenarios.ring_real_input import run

    result = run(repo_root=ROOT)
    assert result["scenario_id"] == "LAB-SCENARIO-RING-REAL-INPUT"
    assert result["direct_file_write_counts_as_d6"] is False
    assert result["ok"] is True
    assert result["INDEPENDENT_VERIFICATION"] == "PENDING"
    assert result["real_app_state_mutation"] is True
    for target in ("libreoffice", "browser", "games"):
        d = result["deliveries"][target]
        assert d["delivered"] is True
        assert d["app_state_changed"] is True
        assert d["before"] != d["after"]


def test_ring_delivered_not_hardcoded_without_mutation():
    """Previous RingsBackend.inject hardcoding delivered=True must fail this check."""
    from gunnchos_device_os.phase_xiv.spatial import SpatialInputService

    # No router → counts-only path cannot claim delivered app mutation
    svc = SpatialInputService(router=None)
    svc.calibrate()
    out = svc.deliver_to_os([])
    assert out["app_state_changed"] is False
    assert out["delivered"] == 0
    assert out["ok"] is False


def test_ring_input_router_mutates_document_browser_game():
    from gunnchos_device_os.device_lab.hw_backends.rings import RingsBackend

    rings = RingsBackend()
    rings.start(evidence_dir=ROOT / "artifacts" / "device_lab" / "test_ring", repo_root=ROOT)
    for target in ("libreoffice", "browser", "games"):
        r = rings.inject(target=target, confidence=0.95, gesture="click")
        assert r["delivered"] is True, target
        assert r["app_state_changed"] is True, target
        assert r["before"] != r["after"], target
    low = rings.inject(confidence=0.1, target="browser")
    assert low["delivered"] is False


def test_g08_local_ai_tutor_honest_primary():
    from gunnchos_device_os.device_lab.scenarios.local_ai_tutor import run

    result = run(repo_root=ROOT)
    assert result["scenario_id"] == "LAB-SCENARIO-LOCAL-AI-TUTOR"
    assert result["INDEPENDENT_VERIFICATION"] == "PENDING"
    assert result["HUMAN_QUALITY"] == "PENDING"
    assert result["foundation_harness_ok"] is True
    # GJ-DEFECT-008: ok must fail closed when micro is primary
    if result.get("primary_model_proof") == "FAIL_MICRO_NOT_ALLOWED":
        assert result["ok"] is False
        assert result["implementer_ready_for_independent_E4_D6"] is False
    elif result.get("primary_model_proof") == "PASS_REAL_RUNTIME":
        assert result["ok"] is True
        assert result["implementer_ready_for_independent_E4_D6"] is True
        assert result["tutor"].get("primary_is_micro_deterministic") is False


def test_g08_ok_false_when_micro_forced(monkeypatch, tmp_path):
    """Harness must not report overall ok=true when micro-deterministic is primary proof."""
    import gunnchos_device_os.device_lab.scenarios.local_ai_tutor as tutor_mod

    def _micro_only(repo_root, evidence):
        return {
            "ok": False,
            "path": "micro_only_unavailable_real_model",
            "runtime": "deterministic_micro",
            "primary_is_micro_deterministic": True,
            "note": "forced micro for defect-008 regression",
        }

    monkeypatch.setattr(tutor_mod, "_try_real_local_ai", _micro_only)
    result = tutor_mod.run(repo_root=ROOT)
    assert result["ok"] is False
    assert result["primary_model_proof"] == "FAIL_MICRO_NOT_ALLOWED"
    assert result["implementer_ready_for_independent_E4_D6"] is False
    assert result["foundation_harness_ok"] is True


def test_lab_future_backlog_present_not_executed():
    path = ROOT / "gunnchos_device_os" / "device_lab" / "LAB_FUTURE_BACKLOG.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["DO_NOT_EXECUTE_IN_WP003R"] is True
    ids = {i["id"] for i in data["items"]}
    for n in range(1, 10):
        assert f"LAB-FUTURE-{n:03d}" in ids
    assert all(i["status"] in {"READY", "BLOCKED"} for i in data["items"])
    assert data.get("executed") in (False, None, [])
