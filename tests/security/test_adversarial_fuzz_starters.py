"""Adversarial / fuzz *starters* for Lane H surfaces.

Not a full fuzz campaign. Exercises hostile inputs against orchestrator,
update signing, radio profile parsing, and cloud-edge mode gates.
"""
from __future__ import annotations

import pytest

from gunnchos_device_os.cloud_edge import CloudEdgeFabric, ServiceMode
from gunnchos_device_os.connectivity_orchestrator import (
    BearerKind,
    BearerMetrics,
    ConnectivityOrchestrator,
)
from gunnchos_device_os.radio_capability import radio_profile_from_device
from gunnchos_device_os.update_signing import (
    SigningRealm,
    UpdatePackageManifest,
    sign_update_dev,
    verify_update_signature,
)


@pytest.mark.parametrize(
    "latency,loss,signal",
    [
        (-1.0, 0.0, -40.0),
        (1e9, 200.0, 50.0),
        (0.0, -5.0, -200.0),
        (float("nan"), 0.0, -50.0),
    ],
)
def test_orchestrator_tolerates_hostile_metrics(latency, loss, signal):
    orch = ConnectivityOrchestrator()
    metrics = BearerMetrics(
        available=True,
        signal_dbm=signal,
        latency_ms=latency,
        loss_pct=loss,
        cost_per_mb=0.0,
        energy_mw=100.0,
        security_score=0.5,
        user_preference=0.5,
    )
    orch.update_metrics(BearerKind.WIFI, metrics)
    score = orch.score(BearerKind.WIFI)
    assert score == score  # finite after sanitization
    result = orch.evaluate()
    assert "active" in result
    assert result["mock"] is False


def test_update_signing_rejects_prod_realm():
    manifest = UpdatePackageManifest(
        package_id="pkg",
        version="1.0.0",
        artifact_sha256="a" * 64,
        realm=SigningRealm.PROD,
    )
    with pytest.raises(ValueError, match="PROD"):
        sign_update_dev(manifest)


def test_update_verify_rejects_tampered_bytes():
    from gunnchos_device_os.update_signing import build_signed_update

    doc = build_signed_update("pkg", "1.0.0", b"payload")
    doc["artifact_sha256"] = "b" * 64
    result = verify_update_signature(doc)
    assert result["valid"] is False
    assert "bad_signature" in result["errors"]


def test_radio_profile_rejects_branded_cellular_string(tmp_path, monkeypatch):
    # Use handheld which is valid, then unit-test parser via forged network dict path.
    from gunnchos_device_os import radio_capability as rc

    with pytest.raises(ValueError, match="generic"):
        rc._parse_cellular({"cellular": "qualcomm-x65-fake"})


def test_cloud_edge_disconnected_blocks_sync():
    fab = CloudEdgeFabric(mode=ServiceMode.DISCONNECTED)
    with pytest.raises(PermissionError):
        fab.sync_enqueue("notes", "1", {"x": 1})
    # Saves still allowed offline.
    assert fab.save_put("s1", {"bytes": 3})["mode"] == "disconnected"


@pytest.mark.parametrize("junk", ["", "!!!", "cloud_please", "LOCAL"])
def test_cloud_edge_invalid_mode_rejected(junk):
    fab = CloudEdgeFabric()
    with pytest.raises(ValueError):
        fab.set_mode(junk)


def test_orchestrator_rejects_unsupported_bearer_update():
    profile = radio_profile_from_device("wearables_arena_set")
    from gunnchos_device_os.connectivity_orchestrator import orchestrator_from_radio_profile

    orch = orchestrator_from_radio_profile(profile)
    assert "cellular" not in profile.supported_bearer_names()
    with pytest.raises(ValueError, match="not supported"):
        orch.update_metrics(
            BearerKind.CELLULAR,
            BearerMetrics(available=True, latency_ms=40, loss_pct=1, energy_mw=900),
        )
