"""Radio capability profiles — profile-driven, no fictional modems."""
from __future__ import annotations

import pytest

from gunnchos_device_os.radio_capability import (
    CellularClass,
    NtnClass,
    radio_capability_matrix,
    radio_profile_from_device,
)
from gunnchos_device_os.connectivity_orchestrator import (
    BearerKind,
    BearerMetrics,
    OrchestratorState,
    orchestrator_for_device,
)


def test_student_profile_wifi_ethernet_cellular_no_ntn():
    p = radio_profile_from_device("student_14_5")
    assert p.wifi_class == "wifi_6e"
    assert p.ethernet_dock is True
    assert p.cellular_class == CellularClass.SIMULATED_GENERIC
    assert p.ntn_class == NtnClass.NONE
    names = p.supported_bearer_names()
    assert "wifi" in names and "ethernet" in names and "cellular" in names
    assert "ntn_simulated" not in names
    assert "qualcomm" not in p.to_dict()["claim_boundary"].lower()
    assert p.to_dict()["mock"] is False


def test_handheld_includes_ntn_simulated():
    p = radio_profile_from_device("handheld_hybrid")
    assert p.ntn_class == NtnClass.SIMULATED
    assert "ntn_simulated" in p.supported_bearer_names()


def test_wearables_wifi_only_path():
    p = radio_profile_from_device("wearables_arena_set")
    names = set(p.supported_bearer_names())
    assert names == {"wifi", "bluetooth", "offline"}


def test_matrix_covers_all_devices():
    matrix = radio_capability_matrix()
    assert "student_14_5" in matrix["devices"]
    assert matrix["mock"] is False
    text = matrix["claim_boundary"].lower()
    assert "no live modem" in text or "no named commercial modem" in text


def test_orchestrator_for_device_handoff_cost_energy():
    orch = orchestrator_for_device("handheld_hybrid")
    orch.update_metrics(
        BearerKind.WIFI,
        BearerMetrics(
            available=True,
            signal_dbm=-50,
            latency_ms=20,
            jitter_ms=4,
            loss_pct=0.5,
            cost_per_mb=0.0,
            energy_mw=400,
            security_score=0.8,
            user_preference=0.7,
        ),
    )
    orch.update_metrics(
        BearerKind.NTN_SIMULATED,
        BearerMetrics(
            available=True,
            signal_dbm=-75,
            latency_ms=400,
            jitter_ms=40,
            loss_pct=2.0,
            cost_per_mb=0.85,
            energy_mw=1200,
            security_score=0.7,
            user_preference=0.2,
        ),
    )
    result = orch.evaluate()
    assert result["active"] == BearerKind.WIFI.value
    delta = orch.handoff_cost_energy(BearerKind.WIFI, BearerKind.NTN_SIMULATED)
    assert delta["cost_delta_per_mb"] > 0
    assert delta["energy_delta_mw"] > 0
    assert delta["mock"] is False


def test_orchestrator_degraded_fault():
    orch = orchestrator_for_device("student_14_5")
    orch.update_metrics(
        BearerKind.WIFI,
        BearerMetrics(
            available=True,
            signal_dbm=-40,
            latency_ms=15,
            jitter_ms=2,
            loss_pct=0,
            cost_per_mb=0,
            energy_mw=300,
            security_score=0.9,
            user_preference=0.8,
        ),
    )
    orch.evaluate()
    orch.inject_fault("degrade_active")
    result = orch.evaluate()
    assert result["state"] in (
        OrchestratorState.DEGRADED.value,
        OrchestratorState.CONNECTED.value,
        OrchestratorState.OFFLINE.value,
    )
    assert "degrade_active" in orch.snapshot()["faults"]


def test_branded_wifi_rejected(monkeypatch):
    from gunnchos_device_os import radio_capability as rc
    from gunnchos_device_os.hardware_profile import DeviceProfile, NetworkCapabilities, DockCapabilities

    class Fake:
        device_id = "x"
        network = NetworkCapabilities(wifi="qualcomm-fastconnect")
        dock = DockCapabilities(supported=False)
        raw = {"network": {"wifi": "qualcomm-fastconnect"}}

    monkeypatch.setattr(rc, "load_device_profile", lambda _id: Fake())
    with pytest.raises(ValueError, match="chip brand"):
        radio_profile_from_device("x")
