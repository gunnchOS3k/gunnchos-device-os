from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.factory_provisioning import (
    FactoryProvisioningStation,
    MacAllocator,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def station(tmp_path):
    return FactoryProvisioningStation(REPO_ROOT, tmp_path / "factory_store.json")


def test_mac_rebind_keeps_address(tmp_path):
    alloc = MacAllocator(tmp_path / "mac_pool.json")
    mac = alloc.allocate("pending")
    assert alloc.rebind(mac, "dev-real") is True
    assert alloc.allocate("dev-real") == mac
    assert alloc._read()["allocated"][mac] == "dev-real"


def test_provision_includes_cert_request_and_esim_external(station):
    result = station.provision_new_device()
    assert result["ok"] is True
    device = station._read()["devices"][result["device_id"]]
    assert device["cert_request"]["status"] == "EXTERNAL_PENDING"
    assert device["cert_request"]["issued_cert_pem"] is None
    assert device["cert_request"]["production_ca"] is False
    assert "BEGIN CERTIFICATE REQUEST" in device["key_injection"]["csr_pem"]
    assert device["key_injection"]["private_key_exported"] is False
    assert device["key_injection"]["hsm_ceremony"] == "EXTERNAL"
    assert device["esim"]["status"] == "EXTERNAL_PENDING"
    assert device["esim"]["iccid"] is None
    assert result["mac"] == device["mac"]
    assert station.mac_allocator._read()["allocated"][result["mac"]] == result["device_id"]
    assert device["PRODUCTION_RELEASE_CLAIMED"] is False


def test_import_test_result_fail_blocks_flash(station):
    result = station.provision_new_device()
    device_id = result["device_id"]
    imported = station.import_test_result(
        device_id,
        {
            "device_id": device_id,
            "station_id": "STATION-1",
            "suite_id": "FINAL_QA",
            "result": "FAIL",
            "timestamp_utc": "2026-08-13T00:00:00Z",
            "measurements": {"boot_probe_ms": 9000},
        },
    )
    assert imported["ok"] is True
    flash = station.flash(device_id, {"realm_id": "FACTORY_PROVISIONING_IMAGE", "image_hash": "abc"})
    assert flash["ok"] is False
    assert flash["error"] == "device_failed_test_refusing_flash"


def test_factory_secure_wipe_clears_secrets_keeps_record(station):
    result = station.provision_new_device()
    device_id = result["device_id"]
    wipe = station.factory_secure_wipe(device_id, reason="rma_return")
    assert wipe["ok"] is True
    assert wipe["physical_media_sanitize"] == "EXTERNAL"
    device = station._read()["devices"][device_id]
    assert device["status"] == "WIPED"
    assert device["identity"]["wiped"] is True
    assert device["key_injection"]["wiped"] is True
    export = station.export_device_record(device_id)
    assert export["ok"] is True
    assert export["record"]["PRODUCTION_RELEASE_CLAIMED"] is False
    flash = station.flash(device_id, {"realm_id": "FACTORY_PROVISIONING_IMAGE"})
    assert flash["ok"] is False


def test_device_record_export_hash_stable_shape(station):
    result = station.provision_new_device()
    export = station.export_device_record(result["device_id"])
    assert "export_sha256" in export["record"]
    assert export["record"]["device"]["test_results"] == []
    assert export["record"]["device"]["wipe_events"] == []
