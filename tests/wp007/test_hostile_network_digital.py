"""HOSTILE_NETWORK_DIGITAL E4 prepared suite."""
from __future__ import annotations

from gunnchos_device_os.security.wp007.hostile_network import (
    HostileNetworkSimulator,
    build_tls_fixture_pair,
)


def test_hostile_network_digital_suite_e4():
    suite = HostileNetworkSimulator().run_digital_suite()
    assert suite["passed"] is True
    assert suite["HOSTILE_NETWORK_DIGITAL"] == "E4_PREPARED"
    assert suite["RF_WIFI_STATUS"] == "E5_E8_EXTERNAL_PENDING"
    assert suite["credential_leak_events"] == []
    ids = {c["case_id"] for c in suite["cases"]}
    assert "HN-DNS-001" in ids
    assert "HN-TLS-001" in ids
    assert "HN-TLS-002" in ids
    assert "HN-TLS-003" in ids
    assert "HN-CAPTIVE-001" in ids
    assert "HN-HTTP-001" in ids
    assert "HN-CRED-001" in ids
    assert "HN-LINK-001" in ids


def test_credentials_never_sent_to_evil_origin():
    sim = HostileNetworkSimulator()
    out = sim.request("https://evil.example/login", with_credentials=True)
    assert out["ok"] is False
    assert out["credentials_sent"] is False


def test_tls_fixture_material_real_x509(tmp_path):
    mat = build_tls_fixture_pair(tmp_path)
    assert mat["expired_not_after_past"] is True
    assert mat["mismatch_san_is_evil"] is True
    assert (tmp_path / "expired.pem").exists()
    assert (tmp_path / "hostname_mismatch.pem").exists()
