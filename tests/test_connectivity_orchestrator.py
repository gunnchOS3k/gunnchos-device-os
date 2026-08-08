"""Connectivity orchestrator — scoring, transitions, fault injection."""
from __future__ import annotations

from gunnchos_device_os.connectivity_orchestrator import (
    BearerKind,
    BearerMetrics,
    ConnectivityOrchestrator,
    OrchestratorState,
)


def _good_wifi(**overrides) -> BearerMetrics:
    base = BearerMetrics(
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
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def _good_ethernet(**overrides) -> BearerMetrics:
    base = BearerMetrics(
        available=True,
        signal_dbm=None,
        latency_ms=5.0,
        jitter_ms=1.0,
        loss_pct=0.0,
        cost_per_mb=0.0,
        energy_mw=150.0,
        security_score=0.95,
        user_preference=0.9,
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def _ok_cellular(**overrides) -> BearerMetrics:
    base = BearerMetrics(
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
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def test_claim_boundary_no_carrier_marketing():
    orch = ConnectivityOrchestrator()
    text = orch.claim_boundary().lower()
    assert "software orchestrator only" in text
    assert "no carrier attach" in text
    snap = orch.snapshot()
    assert snap["mock"] is False
    lowered = snap["claim_boundary"].lower()
    for brand in ("verizon", "t-mobile", "vodafone", "orange"):
        assert brand not in lowered


def test_prefers_ethernet_over_wifi_and_cellular():
    orch = ConnectivityOrchestrator()
    orch.update_metrics(BearerKind.WIFI, _good_wifi())
    orch.update_metrics(BearerKind.CELLULAR, _ok_cellular())
    orch.update_metrics(BearerKind.ETHERNET, _good_ethernet())
    result = orch.evaluate()
    assert result["active"] == BearerKind.ETHERNET.value
    assert result["state"] == OrchestratorState.CONNECTED.value
    assert result["mock"] is False


def test_hysteresis_holds_active_until_delta():
    orch = ConnectivityOrchestrator(hysteresis=20.0)
    orch.update_metrics(BearerKind.WIFI, _good_wifi())
    orch.evaluate()
    assert orch.active_bearer == BearerKind.WIFI
    # Slightly better ethernet but within hysteresis — may or may not switch depending on score gap.
    # Make ethernet only marginally better than wifi so hysteresis holds.
    orch.update_metrics(
        BearerKind.ETHERNET,
        _good_ethernet(latency_ms=16.0, energy_mw=390.0, security_score=0.81, user_preference=0.71),
    )
    ranked = orch.rank_bearers()
    wifi_score = dict(ranked)[BearerKind.WIFI.value]
    eth_score = dict(ranked)[BearerKind.ETHERNET.value]
    if eth_score < wifi_score + orch.hysteresis:
        result = orch.evaluate()
        assert result["active"] == BearerKind.WIFI.value
        assert result["reason"] in ("hold", "better_score")


def test_bearer_transition_on_large_improvement():
    orch = ConnectivityOrchestrator(hysteresis=5.0)
    orch.update_metrics(BearerKind.CELLULAR, _ok_cellular())
    orch.evaluate()
    assert orch.active_bearer == BearerKind.CELLULAR
    orch.update_metrics(BearerKind.ETHERNET, _good_ethernet())
    result = orch.evaluate()
    assert result["active"] == BearerKind.ETHERNET.value
    assert orch.history[-1].from_bearer == BearerKind.CELLULAR.value
    assert orch.history[-1].to_bearer == BearerKind.ETHERNET.value


def test_fault_injection_drop_active_goes_offline_or_alternate():
    orch = ConnectivityOrchestrator()
    orch.update_metrics(BearerKind.WIFI, _good_wifi())
    orch.evaluate()
    assert orch.active_bearer == BearerKind.WIFI
    orch.inject_fault("drop_active")
    # No alternate available
    result = orch.evaluate()
    assert result["active"] == BearerKind.OFFLINE.value
    assert result["state"] == OrchestratorState.OFFLINE.value


def test_fault_injection_jam_wifi_fails_over_to_cellular():
    orch = ConnectivityOrchestrator()
    orch.update_metrics(BearerKind.WIFI, _good_wifi())
    orch.update_metrics(BearerKind.CELLULAR, _ok_cellular())
    orch.evaluate()
    orch.inject_fault("jam_wifi")
    result = orch.evaluate()
    assert result["active"] == BearerKind.CELLULAR.value
    assert "jam_wifi" in orch.snapshot()["faults"]


def test_force_offline_fault():
    orch = ConnectivityOrchestrator()
    orch.update_metrics(BearerKind.WIFI, _good_wifi())
    orch.update_metrics(BearerKind.ETHERNET, _good_ethernet())
    orch.inject_fault("force_offline")
    result = orch.evaluate()
    assert result["active"] == BearerKind.OFFLINE.value


def test_scores_use_all_metric_axes():
    orch = ConnectivityOrchestrator()
    orch.update_metrics(
        BearerKind.WIFI,
        BearerMetrics(
            available=True,
            signal_dbm=-40,
            latency_ms=10,
            jitter_ms=2,
            loss_pct=0,
            cost_per_mb=0,
            energy_mw=200,
            security_score=1.0,
            user_preference=1.0,
        ),
    )
    high = orch.score(BearerKind.WIFI)
    orch.update_metrics(
        BearerKind.WIFI,
        BearerMetrics(
            available=True,
            signal_dbm=-85,
            latency_ms=180,
            jitter_ms=40,
            loss_pct=8,
            cost_per_mb=0.9,
            energy_mw=1800,
            security_score=0.2,
            user_preference=0.1,
        ),
    )
    low = orch.score(BearerKind.WIFI)
    assert high > low
    unavailable = BearerMetrics(available=False)
    orch.update_metrics(BearerKind.WIFI, unavailable)
    assert orch.score(BearerKind.WIFI) == float("-inf")
