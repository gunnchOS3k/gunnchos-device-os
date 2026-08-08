"""Outage survival + resync for the runnable DEV plane client."""
from __future__ import annotations

from gunnchos_device_os.cloud_dev_plane import DevPlaneApp, DevPlaneClient, DevPlaneServer, ServiceMode


def test_outage_queues_and_resync_delivers():
    server = DevPlaneServer(DevPlaneApp(role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.CLOUD)

    # Online write
    assert client.save_put("before-outage", {"n": 0})["save_id"] == "before-outage"

    # Outage: queue sync + enrollment + save
    client.simulate_outage(True)
    q1 = client.sync_enqueue("notes", "n1", {"text": "held"})
    q2 = client.enrollment_submit("dev-outage", "org-dev")
    q3 = client.save_put("during-outage", {"n": 1})
    assert q1["status"] == "held_local"
    assert q2["status"] == "held_local"
    assert q3["status"] == "held_local"
    assert len(client.outbox) == 3

    # Still down — resync refuses
    stuck = client.resync()
    assert stuck["status"] == "still_disconnected"
    assert stuck["outbox_depth"] == 3

    # Recover
    client.simulate_outage(False)
    report = client.resync()
    assert report["status"] == "resync_complete"
    assert report["delivered"] == 3
    assert report["outbox_depth"] == 0

    # Server has the save and can drain sync
    assert client.identity_register  # smoke
    drained = client.sync_drain()
    assert drained["count"] >= 1
    inv = client.inventory()
    assert inv["snapshot"]["saves_count"] >= 2
    assert inv["snapshot"]["enrollment_count"] >= 1
    server.stop()


def test_resync_respects_mode_downgrade():
    server = DevPlaneServer(DevPlaneApp(role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.CLOUD)
    client.simulate_outage(True)
    client.sync_enqueue("notes", "blocked-later", {"x": 1})
    client.simulate_outage(False)
    client.set_mode(ServiceMode.DISCONNECTED)
    report = client.resync()
    assert report["delivered"] == 0
    assert report["failed"] == 1
    assert client.outbox  # remains until mode allows or discarded by operator
    # Local save still works offline without needing resync
    assert client.save_put("offline-ok", {"n": 2})["save_id"] == "offline-ok"
    server.stop()
