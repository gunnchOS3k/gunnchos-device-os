"""Prove LOCAL / DISCONNECTED / CAMPUS_EDGE / CLOUD against runnable DEV plane."""
from __future__ import annotations

import pytest

from gunnchos_device_os.cloud_dev_plane import DevPlaneApp, DevPlaneClient, DevPlaneServer, ServiceMode


@pytest.fixture()
def plane():
    server = DevPlaneServer(DevPlaneApp(role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url)
    yield server, client
    server.stop()


@pytest.mark.parametrize("mode", [ServiceMode.LOCAL, ServiceMode.CAMPUS_EDGE, ServiceMode.CLOUD])
def test_online_modes_full_surface(plane, mode):
    _server, client = plane
    client.set_mode(mode)
    assert client.identity_register("u1", {"role": "student"})["subject_id"] == "u1"
    assert client.identity_resolve("u1")["found"] is True
    enr = client.enrollment_submit("d1", "org1")
    assert enr["status"] == "accepted_dev"
    assert enr["enrollment_token"] == "[REDACTED]"
    assert client.sync_enqueue("workspace", "item-1", {"v": 1})["status"] == "queued"
    drained = client.sync_drain()
    assert drained["count"] == 1
    assert client.save_put("save-1", {"size": 10})["save_id"] == "save-1"
    client.matchmaking_publish("lobby-1", {"game": "arena", "slots": 4})
    client.telemetry_emit("heartbeat", {"ok": True})
    client.update_metadata_set("evt-alpha", "0.2.0", {"ring": "canary"})
    hb = client.fleet_heartbeat("fleet-1", ring="dev")
    assert hb["device_id"] == "fleet-1"
    diag = client.diagnostics_report("fleet-1", {"disk_ok": True})
    assert diag["device_id"] == "fleet-1"
    inv = client.inventory()
    assert inv["realm"] == "DEV"
    assert "identity" in inv["service_list"]
    assert inv["mock"] is False


def test_disconnected_identity_saves_diagnostics_only(plane):
    _server, client = plane
    client.set_mode(ServiceMode.DISCONNECTED)
    client.identity_register("offline-user")
    client.save_put("local-save", {"n": 1})
    client.diagnostics_report("offline-dev", {"ok": True})
    with pytest.raises(PermissionError):
        client.enrollment_submit("d", "o")
    with pytest.raises(PermissionError):
        client.telemetry_emit("x", {})
    with pytest.raises(PermissionError):
        client.matchmaking_publish("L", {})
    with pytest.raises(PermissionError):
        client.update_metadata_set("ch", "1.0.0")
    with pytest.raises(PermissionError):
        client.sync_enqueue("c", "i", {})
    with pytest.raises(PermissionError):
        client.fleet_heartbeat("f1")


def test_claim_boundary_and_ports(plane):
    server, client = plane
    inv = client.inventory()
    assert "DEV" in inv["claim_boundary"] or "dev" in inv["claim_boundary"].lower()
    assert inv["ports"]["gateway"] == 8100
    assert server.app.role == "gateway"
