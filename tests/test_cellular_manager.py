"""Cellular manager — SIM/eSIM interface, APN, IP/DNS, airplane, recovery."""
from __future__ import annotations

from gunnchos_device_os.connectivity.cellular_manager import CellularManager, PdnType
from gunnchos_device_os.connectivity.honest_tokens import (
    CARRIER_ACCEPTED,
    REAL_ESIM_CREDENTIALS,
    STANDARDIZED_6G,
)


def test_full_bringup_is_simulated_not_carrier_accepted():
    mgr = CellularManager()
    result = mgr.full_bringup()
    assert result["ok"] is True
    assert result["physical_attach"] is False
    assert result["simulated"] is True
    assert result["STANDARDIZED_6G"] is False
    assert result["CARRIER_ACCEPTED"] is False
    assert result["RM520N_GL_NTN"] is False
    assert result["REAL_ESIM_CREDENTIALS"] == "EXTERNAL"
    ip = result["attach"]["ip"]
    assert ip["ipv4"]
    assert ip["ipv6"]
    assert ip["dns_v4"]
    assert ip["dns_v6"]
    assert ip["active"] is True


def test_esim_interface_never_stores_credentials():
    mgr = CellularManager()
    listed = mgr.esim.list_profiles()
    assert listed["REAL_ESIM_CREDENTIALS"] == REAL_ESIM_CREDENTIALS
    assert listed["CARRIER_ACCEPTED"] is False
    download = mgr.esim.request_download("LPA:1$example$SECRET")
    assert download["ok"] is False
    assert download["status"] == "EXTERNAL_PENDING"
    assert "SECRET" not in str(download)
    assert mgr.esim.last_request["activation_code"] is None
    enable = mgr.esim.enable_profile("89000000000000000000")
    assert enable["ok"] is False
    assert enable["status"] == "EXTERNAL_PENDING"


def test_apn_ipv4_only_and_ipv6_only():
    mgr = CellularManager()
    mgr.full_bringup()
    mgr.set_apn("ims", pdn_type=PdnType.IPV4)
    att = mgr.attach_pdn()
    assert att["ip"]["ipv4"]
    assert att["ip"]["ipv6"] is None
    mgr.set_apn("ims", pdn_type="ipv6")
    att6 = mgr.attach_pdn()
    assert att6["ip"]["ipv4"] is None
    assert att6["ip"]["ipv6"]
    assert att6["CARRIER_ACCEPTED"] is False


def test_airplane_blocks_register_and_recover():
    mgr = CellularManager()
    air = mgr.set_airplane(True)
    assert air["airplane"] is True
    assert mgr.register()["ok"] is False
    assert mgr.attach_pdn()["ok"] is False
    assert mgr.recover()["ok"] is False
    mgr.set_airplane(False)
    assert mgr.full_bringup()["ok"] is True


def test_recovery_re_registers():
    mgr = CellularManager()
    assert mgr.full_bringup()["ok"] is True
    recovered = mgr.recover()
    assert recovered["ok"] is True
    assert recovered["recovery_attempts"] == 1
    assert recovered["CARRIER_ACCEPTED"] is False
    assert mgr.ip.active is True


def test_tokens_module_constants():
    assert STANDARDIZED_6G is False
    assert CARRIER_ACCEPTED is False
