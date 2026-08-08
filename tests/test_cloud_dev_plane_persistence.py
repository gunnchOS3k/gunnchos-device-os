"""SQLite persistence + multi-instance / failure tests for cloud DEV plane."""
from __future__ import annotations

import threading
from pathlib import Path

from gunnchos_device_os.cloud_dev_plane import DevPlaneApp, DevPlaneClient, DevPlaneServer, ServiceMode
from gunnchos_device_os.cloud_dev_plane.store import DevPlaneStore


def test_sqlite_persistence_survives_reopen(tmp_path: Path):
    db = tmp_path / "plane.sqlite3"
    store = DevPlaneStore(db, backend="sqlite")
    server = DevPlaneServer(DevPlaneApp(store=store, role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.LOCAL)
    assert client.identity_register("subj-sqlite", {"email": "a@dev.local"})["subject_id"] == "subj-sqlite"
    assert client.save_put("save-1", {"n": 1})["save_id"] == "save-1"
    snap = client.inventory()["snapshot"]
    assert snap["backend"] == "sqlite"
    assert snap["identity_count"] >= 1
    assert snap["saves_count"] >= 1
    server.stop()
    store.close()

    store2 = DevPlaneStore(db, backend="sqlite")
    snap2 = store2.snapshot()
    assert snap2["backend"] == "sqlite"
    assert snap2["identity_count"] >= 1
    assert snap2["saves_count"] >= 1
    assert "subj-sqlite" in store2.data["identities"]
    store2.close()


def test_multi_instance_shared_sqlite_and_failover(tmp_path: Path):
    db = tmp_path / "shared.sqlite3"
    store_a = DevPlaneStore(db, backend="sqlite")
    store_b = DevPlaneStore(db, backend="sqlite")
    server_a = DevPlaneServer(DevPlaneApp(store=store_a, role="gateway")).start()
    server_b = DevPlaneServer(DevPlaneApp(store=store_b, role="gateway")).start()
    client_a = DevPlaneClient(base_url=server_a.base_url, mode=ServiceMode.CLOUD)
    client_b = DevPlaneClient(base_url=server_b.base_url, mode=ServiceMode.CLOUD)

    client_a.identity_register("multi-a", {"role": "writer"})
    # Instance B must observe durable write
    inv_b = client_b.inventory()
    assert inv_b["snapshot"]["identity_count"] >= 1

    client_b.save_put("from-b", {"ok": True})
    inv_a = client_a.inventory()
    assert inv_a["snapshot"]["saves_count"] >= 1

    # Failure: stop A; B continues
    server_a.stop()
    store_a.close()
    assert client_b.enrollment_submit("dev-fail", "org-dev")["status"] == "accepted_dev"
    assert client_b.inventory()["snapshot"]["enrollment_count"] >= 1

    server_b.stop()
    store_b.close()


def test_concurrent_multi_instance_writes(tmp_path: Path):
    db = tmp_path / "concurrent.sqlite3"
    errors: list[str] = []

    def worker(n: int) -> None:
        try:
            store = DevPlaneStore(db, backend="sqlite")
            server = DevPlaneServer(DevPlaneApp(store=store, role="gateway")).start()
            client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.LOCAL)
            for i in range(8):
                client.save_put(f"w{n}-{i}", {"worker": n, "i": i})
            server.stop()
            store.close()
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors

    final = DevPlaneStore(db, backend="sqlite")
    assert final.snapshot()["saves_count"] >= 32
    final.close()
