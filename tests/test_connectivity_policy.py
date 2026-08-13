"""Multi-bearer policy — failover, offline, reconnect, airplane, NTN taxonomy."""
from __future__ import annotations

import pytest

from gunnchos_device_os.connectivity.bearers import (
    FutureNtnCapableModem,
    NtnPathClass,
    build_default_bearers,
    ntn_taxonomy,
    select_bearer,
)
from gunnchos_device_os.connectivity.honest_tokens import honest_tokens
from gunnchos_device_os.connectivity.policy import MultiBearerPolicy
from gunnchos_device_os.connectivity_orchestrator import BearerKind, BearerMetrics


def _wifi() -> BearerMetrics:
    return BearerMetrics(
        available=True,
        signal_dbm=-45.0,
        latency_ms=18.0,
        jitter_ms=3.0,
        loss_pct=0.2,
        cost_per_mb=0.0,
        energy_mw=400.0,
        security_score=0.8,
        user_preference=0.7,
    )


def _cellular() -> BearerMetrics:
    return BearerMetrics(
        available=True,
        signal_dbm=-70.0,
        latency_ms=45.0,
        jitter_ms=12.0,
        loss_pct=1.0,
        cost_per_mb=0.4,
        energy_mw=900.0,
        security_score=0.85,
        user_preference=0.4,
    )


def test_honest_tokens_never_claim_6g_or_carrier():
    tokens = honest_tokens()
    assert tokens["STANDARDIZED_6G"] is False
    assert tokens["CARRIER_ACCEPTED"] is False
    assert tokens["RM520N_GL_NTN"] is False
    assert tokens["RM520N_GL_6G"] is False
    assert tokens["DOCK_TB5"] is False
    assert tokens["DOCK_TB4"] is True
    assert tokens["REAL_ESIM_CREDENTIALS"] == "EXTERNAL"


def test_bluetooth_is_not_wan_failover():
    bearers = build_default_bearers()
    bearers["bluetooth"].connect()
    choice = select_bearer(bearers)
    assert choice["active"] == "offline"
    bearers["wifi"].connect()
    assert select_bearer(bearers)["active"] == "wifi"


def test_ntn_taxonomy_three_classes():
    tax = ntn_taxonomy()
    assert tax["terrestrial"]["sku"] == "RM520N-GL"
    assert tax["terrestrial"]["ntn"] is False
    assert tax["future_ntn_capable_modem"]["selected"] is False
    assert tax["future_ntn_capable_modem"]["not_rm520n_gl"] is True
    assert tax["software_ntn_simulation"]["simulated"] is True
    assert tax["software_ntn_simulation"]["live_ntn"] is False
    assert tax["STANDARDIZED_6G"] is False
    future = FutureNtnCapableModem()
    assert future.ntn_path_class == NtnPathClass.FUTURE_NTN_CAPABLE_MODEM.value
    assert future.connect()["ok"] is False
    assert future.connect()["not_rm520n_gl"] is True


def test_failover_wifi_to_cellular_then_offline():
    policy = MultiBearerPolicy()
    policy.apply_metrics(BearerKind.WIFI, _wifi())
    policy.apply_metrics(BearerKind.CELLULAR, _cellular())
    first = policy.evaluate()
    assert first["active"] == BearerKind.WIFI.value
    fail = policy.failover(drop=BearerKind.WIFI.value)
    assert fail["to"] == BearerKind.CELLULAR.value
    fail2 = policy.failover(drop=BearerKind.CELLULAR.value)
    assert fail2["to"] == BearerKind.OFFLINE.value
    assert fail2["offline"] is True
    assert fail2["STANDARDIZED_6G"] is False
    assert fail2["CARRIER_ACCEPTED"] is False


def test_reconnect_restores_last_wan():
    policy = MultiBearerPolicy()
    policy.apply_metrics(BearerKind.WIFI, _wifi())
    policy.evaluate()
    policy.failover(drop=BearerKind.WIFI.value)
    assert policy.orch.active_bearer == BearerKind.OFFLINE
    policy.apply_metrics(BearerKind.WIFI, _wifi())
    recon = policy.reconnect()
    assert recon["active"] == BearerKind.WIFI.value
    assert recon["reconnect_count"] == 1


def test_airplane_forces_offline_and_blocks_reconnect():
    policy = MultiBearerPolicy()
    policy.apply_metrics(BearerKind.WIFI, _wifi())
    policy.evaluate()
    air = policy.set_airplane(True)
    assert air["airplane"] is True
    assert air["active"] == BearerKind.OFFLINE.value
    bt = policy.enable_bluetooth_during_airplane()
    assert bt["bluetooth_pan"] is True
    assert bt["wan_active"] == BearerKind.OFFLINE.value
    recon = policy.reconnect()
    assert recon["ok"] is False
    assert recon["reason"] == "airplane"


def test_bluetooth_cannot_be_wan():
    with pytest.raises(ValueError, match="bluetooth_as_wan"):
        MultiBearerPolicy(bluetooth_as_wan=True)


def test_ethernet_declares_tb4_not_tb5():
    bearers = build_default_bearers()
    connected = bearers["ethernet"].connect()
    assert connected["dock_tb4"] is True
    assert connected["dock_tb5"] is False
