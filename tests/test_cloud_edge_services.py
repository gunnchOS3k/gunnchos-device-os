"""Cloud/edge fabric stubs — LOCAL / DISCONNECTED / CAMPUS_EDGE / CLOUD."""
from __future__ import annotations

import pytest

from gunnchos_device_os.cloud_edge import CloudEdgeFabric, ServiceMode


@pytest.mark.parametrize(
    "mode",
    [ServiceMode.LOCAL, ServiceMode.CAMPUS_EDGE, ServiceMode.CLOUD],
)
def test_online_modes_full_surface(mode):
    fab = CloudEdgeFabric()
    fab.set_mode(mode)
    fab.identity_register("u1", {"role": "student"})
    assert fab.identity_resolve("u1")["found"] is True
    enr = fab.enrollment_submit("d1", "org1")
    assert enr["status"] == "accepted_stub"
    fab.sync_enqueue("workspace", "item-1", {"v": 1})
    drained = fab.sync_drain()
    assert drained[0]["status"] == "delivered_stub"
    assert fab.save_put("save-1", {"size": 10})["save_id"] == "save-1"
    fab.matchmaking_publish("lobby-1", {"game": "arena", "slots": 4})
    assert fab.matchmaking_list()["lobbies"]
    fab.telemetry_emit("heartbeat", {"ok": True})
    fab.update_metadata_set("evt-alpha", "0.2.0", {"ring": "canary"})
    assert fab.update_metadata_get("evt-alpha")["found"] is True
    snap = fab.snapshot()
    assert snap["mode"] == mode.value
    assert snap["mock"] is False


def test_disconnected_allows_identity_and_saves_only():
    fab = CloudEdgeFabric(mode=ServiceMode.DISCONNECTED)
    fab.identity_register("offline-user")
    fab.save_put("local-save", {"n": 1})
    with pytest.raises(PermissionError):
        fab.enrollment_submit("d", "o")
    with pytest.raises(PermissionError):
        fab.telemetry_emit("x", {})
    with pytest.raises(PermissionError):
        fab.matchmaking_publish("L", {})
    with pytest.raises(PermissionError):
        fab.update_metadata_set("ch", "1.0.0")


def test_claim_boundary():
    fab = CloudEdgeFabric()
    assert "stubs only" in fab.claim_boundary().lower()
