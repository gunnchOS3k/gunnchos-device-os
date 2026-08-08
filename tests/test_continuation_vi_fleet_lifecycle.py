"""Cont VI — cloud/fleet lifecycle against SQLite DEV plane."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cloud_dev_plane import DevPlaneApp, DevPlaneClient, DevPlaneServer, ServiceMode
from gunnchos_device_os.cloud_dev_plane.store import DevPlaneStore


def _plane(tmp_path: Path):
    db = tmp_path / "fleet-life.sqlite3"
    store = DevPlaneStore(db, backend="sqlite")
    server = DevPlaneServer(DevPlaneApp(store=store, role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.CLOUD)
    return store, server, client


def test_fleet_lifecycle_enroll_revoke_campaigns_stale_telemetry(tmp_path: Path):
    store, server, client = _plane(tmp_path)
    try:
        # service restart simulation: reopen store
        assert client.enrollment_submit("dev-1", "org-dev")["status"] == "accepted_dev"
        # duplicate enrollment (idempotent overwrite)
        dup = client.enrollment_submit("dev-1", "org-dev")
        assert dup["status"] == "accepted_dev"

        client.fleet_heartbeat("dev-1", ring="dev")
        inv = client.fleet_inventory()
        assert any(d["device_id"] == "dev-1" for d in inv["devices"])

        ota = client.fleet_ota_campaign(version="0.1.2", cohort="pilot")
        assert ota["kind"] == "ota"
        rb = client.fleet_rollback_campaign(target_version="0.1.0")
        assert rb["kind"] == "rollback"

        client.fleet_mark_stale("dev-1")
        stale = client.fleet_stale()
        assert any(d["device_id"] == "dev-1" for d in stale["stale"])

        for i in range(5):
            client.telemetry_emit("metric", {"i": i, "backlog": True})
        backlog = client.telemetry_backlog()
        assert backlog["count"] >= 5

        diag = client.diagnostics_request("dev-1", {"net": True})
        assert diag["status"] == "queued_dev"

        revoked = client.enrollment_revoke("dev-1")
        assert revoked["status"] == "revoked"

        # host restart: reopen sqlite
        server.stop()
        store.close()
        store2 = DevPlaneStore(tmp_path / "fleet-life.sqlite3", backend="sqlite")
        assert "dev-1" in store2.data["enrollments"]
        assert store2.data["enrollments"]["dev-1"]["status"] == "revoked"
        assert store2.data.get("campaigns")
        store2.close()
    finally:
        try:
            server.stop()
        except Exception:
            pass
        try:
            store.close()
        except Exception:
            pass


def test_multi_instance_and_save_conflict(tmp_path: Path):
    db = tmp_path / "multi.sqlite3"
    store_a = DevPlaneStore(db, backend="sqlite")
    store_b = DevPlaneStore(db, backend="sqlite")
    server_a = DevPlaneServer(DevPlaneApp(store=store_a, role="gateway")).start()
    server_b = DevPlaneServer(DevPlaneApp(store=store_b, role="gateway")).start()
    a = DevPlaneClient(base_url=server_a.base_url, mode=ServiceMode.CLOUD)
    b = DevPlaneClient(base_url=server_b.base_url, mode=ServiceMode.CLOUD)
    try:
        first = a.save_put_versioned("save-x", {"version": 1, "score": 10})
        assert first["meta"]["version"] == 1
        conflict = b.save_put_versioned("save-x", {"version": 2, "score": 99}, expect_version=0)
        assert conflict.get("status") == "conflict" or conflict.get("http_status") == 409
        ok = b.save_put_versioned("save-x", {"version": 2, "score": 11}, expect_version=1)
        assert ok.get("meta", {}).get("version") == 2

        # scale-ish: many devices
        for i in range(25):
            a.enrollment_submit(f"scale-{i}", "org-dev")
            a.fleet_heartbeat(f"scale-{i}")
        inv = b.fleet_inventory()
        assert len(inv["devices"]) >= 20
    finally:
        server_a.stop()
        server_b.stop()
        store_a.close()
        store_b.close()


def test_offline_recovery_telemetry_backlog(tmp_path: Path):
    store, server, client = _plane(tmp_path)
    try:
        client.simulate_outage(True)
        held = client.telemetry_emit("offline_event", {"n": 1})
        assert held["status"] == "held_local"
        client.simulate_outage(False)
        resync = client.resync()
        assert resync["delivered"] >= 1
        assert client.telemetry_backlog()["count"] >= 1
    finally:
        server.stop()
        store.close()
