"""WP007-IV-RES-001 — UpdaterService asymmetric cryptographic verification."""
from __future__ import annotations

import base64

from gunnchos_device_os.runtime.adapters import UpdaterService
from gunnchos_device_os.runtime.service_base import ServiceConfig
from gunnchos_device_os.security.wp007 import update_trust


def _svc() -> UpdaterService:
    svc = UpdaterService(ServiceConfig(service_id="updater", options={"channel": "dev"}))
    svc.on_start()
    return svc


def test_happy_path_real_ed25519_verify():
    svc = _svc()
    assert svc.api_verify()["verified"] is False
    svc.api_download(version="0.2.0")
    out = svc.api_verify()
    assert out["verified"] is True
    assert out["reason"] == "ok"
    assert out["trust_realm"] == update_trust.DEV_TEST_TRUST_ROOT
    assert out["production_keys_used"] is False
    assert out["PRODUCTION_TRUST_ROOT"] == "EXTERNAL_PENDING"


def test_force_verified_cannot_override():
    svc = _svc()
    forced = svc.api_verify(force_verified=True)
    assert forced["verified"] is False
    assert forced["reason"] == "no_package"
    svc.api_download(version="0.2.1")
    # Even with force flag, success still requires real crypto
    ok = svc.api_verify(force_verified=True)
    assert ok["verified"] is True
    # Tamper then force still fails
    pkg = dict(svc._store["package"])
    pkg["digest_sha256"] = "b" * 64
    svc._store["package"] = pkg
    bad = svc.api_verify(force_verified=True)
    assert bad["verified"] is False
    assert bad["reason"] == "signature_invalid"


def test_wrong_key_fails():
    pkg = update_trust.sign_update_package(
        version="1.0.0",
        security_version=1,
        digest_sha256="c" * 64,
        metadata={"channel": "dev"},
        private_key=update_trust.alternate_untrusted_private_key(),
    )
    result = update_trust.verify_update_package(pkg)
    assert result.verified is False
    assert result.reason == "signature_invalid"


def test_modified_payload_fails():
    pkg = update_trust.sign_update_package(
        version="1.0.0",
        security_version=1,
        digest_sha256="d" * 64,
        metadata={"channel": "dev"},
    )
    pkg["digest_sha256"] = "e" * 64
    result = update_trust.verify_update_package(pkg)
    assert result.verified is False
    assert result.reason == "signature_invalid"


def test_modified_metadata_fails():
    pkg = update_trust.sign_update_package(
        version="1.0.0",
        security_version=1,
        digest_sha256="f" * 64,
        metadata={"channel": "dev", "size_bytes": 1},
    )
    pkg["metadata"] = {"channel": "dev", "size_bytes": 999}
    result = update_trust.verify_update_package(pkg)
    assert result.verified is False
    assert result.reason == "signature_invalid"


def test_missing_and_malformed_signature_fail():
    pkg = update_trust.sign_update_package(
        version="1.0.0",
        security_version=1,
        digest_sha256="a" * 64,
        metadata={},
    )
    missing = dict(pkg)
    missing.pop("signature_b64")
    assert update_trust.verify_update_package(missing).reason == "missing_signature"
    malformed = dict(pkg)
    malformed["signature_b64"] = "%%%not-base64%%%"
    assert update_trust.verify_update_package(malformed).reason == "malformed_signature"
    short = dict(pkg)
    short["signature_b64"] = base64.b64encode(b"short").decode()
    assert update_trust.verify_update_package(short).reason == "malformed_signature"


def test_rollback_version_fails():
    pkg = update_trust.sign_update_package(
        version="0.0.1",
        security_version=1,
        digest_sha256="a" * 64,
        metadata={},
    )
    result = update_trust.verify_update_package(pkg, active_security_version=5)
    assert result.verified is False
    assert result.reason == "anti_rollback_security_version"


def test_production_realm_external_pending():
    pkg = update_trust.sign_update_package(
        version="1.0.0",
        security_version=1,
        digest_sha256="a" * 64,
        metadata={},
    )
    pkg["trust_realm"] = update_trust.PRODUCTION_TRUST_ROOT
    result = update_trust.verify_update_package(pkg)
    assert result.verified is False
    assert result.reason == "production_trust_external_pending"


def test_trust_metadata_pins_public_key_no_prod_private():
    meta = update_trust.trust_metadata()
    assert meta["PRODUCTION_TRUST_ROOT"] == "EXTERNAL_PENDING"
    assert meta["production_private_key_committed"] is False
    assert meta["DEV_TEST_TRUST_ROOT"]["public_key_b64"] == update_trust.pinned_dev_public_key_b64()
    assert meta["DEV_TEST_TRUST_ROOT"]["algorithm"] == "Ed25519"


def test_stage_requires_verified():
    svc = _svc()
    svc.api_download(version="0.3.0")
    svc._store["verified"] = False
    assert svc.api_stage()["staged"] is False
    assert svc.api_verify()["verified"] is True
    assert svc.api_stage()["staged"] is True
