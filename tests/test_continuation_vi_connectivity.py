"""Cont VI — connectivity bearers + RM520N-GL simulated modem."""
from __future__ import annotations

from gunnchos_device_os.connectivity.bearers import (
    FutureNTNBearer,
    SimulatedNTNBearer,
    TerrestrialBearer,
    build_default_bearers,
    select_bearer,
)
from gunnchos_device_os.connectivity.modem_rm520n import ModemManagerFacade, SimulatedRM520NGL
from gunnchos_device_os.runtime.adapters import build_service
from gunnchos_device_os.runtime.service_base import ServiceConfig


def test_bearer_set_and_no_fake_current_ntn():
    bearers = build_default_bearers()
    assert set(bearers) == {"ethernet", "wifi", "terrestrial", "future_ntn", "ntn_simulated"}
    future = bearers["future_ntn"]
    assert isinstance(future, FutureNTNBearer)
    assert future.supported is False
    assert future.connect()["fake_current_ntn"] is False
    assert future.connect()["ok"] is False

    sim = bearers["ntn_simulated"]
    assert isinstance(sim, SimulatedNTNBearer)
    assert sim.connect()["simulated"] is True
    assert sim.connect()["fake_current_ntn"] is False

    terr = bearers["terrestrial"]
    assert isinstance(terr, TerrestrialBearer)
    assert terr.connect()["ntn_claimed"] is False


def test_select_bearer_preference():
    bearers = build_default_bearers()
    bearers["wifi"].connect()
    bearers["terrestrial"].connect()
    choice = select_bearer(bearers)
    assert choice["active"] == "wifi"
    bearers["ethernet"].connect()
    assert select_bearer(bearers)["active"] == "ethernet"


def test_rm520n_gl_simulated_fixture():
    modem = SimulatedRM520NGL()
    enum = modem.enumerate()
    assert enum["sku"] == "RM520N-GL"
    assert enum["ntn_claimed"] is False
    facade = ModemManagerFacade(modem)
    attach = facade.full_attach()
    assert attach["ok"] is True
    assert attach["ntn_claimed"] is False
    diag = modem.diagnostics()
    assert diag["firmware_version"]
    assert diag["sim"]["ready"] is True
    assert modem.reconnect()["ok"] is True
    assert modem.enable_gnss(True)["gnss_enabled"] is True


def test_connectivity_service_modem_and_bearers():
    svc = build_service("connectivity", ServiceConfig("connectivity"))
    assert svc.start().state.value == "running"
    listed = svc.api("list_bearers")
    assert listed["future_ntn_fake_current"] is False
    assert "future_ntn" in listed["bearers"]
    attach = svc.api("modem_rm520n", action="full_attach")
    assert attach["ok"] is True
    choice = svc.api("route_choice")
    assert choice["active"] in ("terrestrial", "wifi", "ethernet", "ntn_simulated", "offline")
    offline = svc.api("degraded_offline")
    assert offline["offline"] is True
