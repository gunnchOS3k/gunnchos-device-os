"""DEV-only update signing tests."""
from __future__ import annotations

import copy

import pytest

from gunnchos_device_os.update_signing import (
    SigningRealm,
    UpdatePackageManifest,
    build_signed_update,
    sign_update_dev,
    verify_update_signature,
)


def test_build_and_verify_dev_update():
    doc = build_signed_update("gunnchos-core", "0.2.0-dev", b"artifact-bytes", channel="evt-alpha")
    assert doc["realm"] == "dev"
    assert doc["signature"]
    assert doc["mock"] is False
    assert "no production" in doc["claim_boundary"].lower()
    result = verify_update_signature(doc)
    assert result["valid"] is True


def test_tamper_fails():
    doc = build_signed_update("pkg", "1.0.0", b"x")
    bad = copy.deepcopy(doc)
    bad["version"] = "9.9.9"
    assert verify_update_signature(bad)["valid"] is False


def test_prod_verify_rejected():
    doc = build_signed_update("pkg", "1.0.0", b"x")
    doc["realm"] = SigningRealm.PROD.value
    result = verify_update_signature(doc)
    assert result["valid"] is False
    assert "prod_realm_rejected_no_production_keys" in result["errors"]


def test_sign_rejects_prod_manifest():
    m = UpdatePackageManifest(
        package_id="p",
        version="1",
        artifact_sha256="c" * 64,
        realm=SigningRealm.PROD,
    )
    with pytest.raises(ValueError):
        sign_update_dev(m)
