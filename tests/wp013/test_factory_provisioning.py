from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.factory_provisioning import (
    FactoryProvisioningStation,
    MacAllocator,
    generate_serial,
    validate_calibration_record,
)
from gunnchos_device_os.release_engineering.os_image_builder import RealmImageBuilder

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_generate_serial_is_dev_test_marked_and_deterministic():
    s1 = generate_serial(1, line_id="L1", product_code="GX1")
    s2 = generate_serial(1, line_id="L1", product_code="GX1")
    assert s1 == s2
    assert s1.startswith("DEVTEST-")
    assert generate_serial(2) != generate_serial(1)


def test_generate_serial_rejects_negative_sequence():
    with pytest.raises(ValueError):
        generate_serial(-1)


def test_mac_allocator_uses_locally_administered_range_only(tmp_path):
    alloc = MacAllocator(tmp_path / "mac_pool.json")
    mac1 = alloc.allocate("dev-1")
    mac2 = alloc.allocate("dev-2")
    assert mac1 != mac2
    assert alloc.is_locally_administered(mac1)
    assert alloc.is_locally_administered(mac2)
    # Re-allocating the same device returns the same MAC (idempotent).
    assert alloc.allocate("dev-1") == mac1


def test_mac_allocator_release_frees_address(tmp_path):
    alloc = MacAllocator(tmp_path / "mac_pool.json")
    mac = alloc.allocate("dev-1")
    assert alloc.release(mac) is True
    assert alloc.release(mac) is False


def test_validate_calibration_record():
    good = {
        "device_id": "dev-1",
        "test_station_id": "STATION-3",
        "measurements": {"battery_v": 4.1},
        "result": "PASS",
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }
    assert validate_calibration_record(good) == []
    bad = {"device_id": "dev-1"}
    failures = validate_calibration_record(bad)
    assert "missing_field:test_station_id" in failures


@pytest.fixture()
def station(tmp_path):
    return FactoryProvisioningStation(REPO_ROOT, tmp_path / "factory_store.json")


def test_provision_new_device_creates_identity_mac_key_esim(station):
    result = station.provision_new_device()
    assert result["ok"] is True
    device_id = result["device_id"]

    data = station._read()
    device = data["devices"][device_id]
    assert device["identity"]["dummy_identity"] is True
    assert device["key_injection"]["production_key"] is False
    assert device["esim"]["status"] == "EXTERNAL_PENDING"
    assert device["status"] == "PROVISIONED"


def test_calibration_failure_blocks_flash(station):
    result = station.provision_new_device()
    device_id = result["device_id"]

    fail_record = {
        "device_id": device_id,
        "test_station_id": "STATION-1",
        "measurements": {"battery_v": 2.0},
        "result": "FAIL",
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }
    cal = station.import_calibration(device_id, fail_record)
    assert cal["ok"] is True

    flash = station.flash(device_id, {"realm_id": "FACTORY_PROVISIONING_IMAGE", "image_hash": "abc"})
    assert flash["ok"] is False
    assert flash["error"] == "device_failed_calibration_refusing_flash"


def test_flash_and_post_flash_verify_uses_real_build_manifest(station, tmp_path):
    result = station.provision_new_device()
    device_id = result["device_id"]

    pass_record = {
        "device_id": device_id,
        "test_station_id": "STATION-1",
        "measurements": {"battery_v": 4.2},
        "result": "PASS",
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }
    station.import_calibration(device_id, pass_record)

    builder = RealmImageBuilder(REPO_ROOT)
    build_result = builder.build("factory", unsigned=False)
    manifest = builder.inspect("factory")["manifest"]

    flash = station.flash(device_id, manifest)
    assert flash["ok"] is True
    verify = station.post_flash_verify(device_id)
    assert verify["ok"] is True
    assert verify["last_flash_event"]["image_hash"] == build_result["image_hash"]


def test_refuses_to_flash_a_production_release_claim(station):
    result = station.provision_new_device()
    device_id = result["device_id"]
    bad_manifest = {"realm_id": "PRODUCTION_SHIPPING_IMAGE_DEFINITION", "PRODUCTION_RELEASE_CLAIMED": True}
    flash = station.flash(device_id, bad_manifest)
    assert flash["ok"] is False
    assert flash["error"] == "refusing_to_flash_production_release_claim"


def test_export_device_record_includes_export_hash(station):
    result = station.provision_new_device()
    device_id = result["device_id"]
    export = station.export_device_record(device_id)
    assert export["ok"] is True
    assert "export_sha256" in export["record"]
    assert export["record"]["device"]["device_id"] == device_id


def test_repair_traceability_log(station):
    result = station.provision_new_device()
    device_id = result["device_id"]
    event = station.record_repair_event(device_id, component="battery", technician_id="tech-7", reason="swollen_cell")
    assert event["ok"] is True
    history = station.repair_history(device_id)
    assert len(history) == 1
    assert history[0]["component"] == "battery"


def test_wipe_and_rework_releases_serial_and_mac(station):
    result = station.provision_new_device()
    device_id = result["device_id"]
    mac_before = result["mac"]

    wipe = station.wipe_and_rework(device_id, reason="failed_final_qa")
    assert wipe["ok"] is True
    assert wipe["released_mac"] == mac_before

    data = station._read()
    assert device_id not in data["devices"]
    # MAC pool must have released the address for reuse.
    assert mac_before not in station.mac_allocator._read()["allocated"]
