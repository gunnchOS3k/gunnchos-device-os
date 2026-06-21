"""Tests for Edge-IO contract."""
from gunnchos_device_os.edge_io_contract import export_session, get_contract, start_field_session


def test_contract_metrics():
    c = get_contract()
    assert "timestamp" in c["metrics"]
    assert c["session"]["no_private_packet_payloads"] is True


def test_consent_required():
    r = start_field_session("u1", "ds_xl_coder", consent=False)
    assert r["started"] is False
    assert r["user_message"]


def test_export_formats():
    r = export_session("s1", "json")
    assert r["exported"] is True
