"""Fail-closed tests for GuestServiceForward v1 + QEMU usernet assembly."""
from __future__ import annotations

import json
import os

import pytest

from gunnchos_device_os.device_lab.guest_service_forward import (
    GuestForwardRule,
    GuestServiceForwardError,
    apply_guest_service_forward_env,
    build_usernet_netdev,
    device_lab_hub_httpd_forward,
    parse_guestfwd_env,
    resolve_boot_usernet_netdev,
    guestfwd_proof_service_forward,
    validate_guest_forward_rule,
    validate_guest_forward_rules,
)
from gunnchos_device_os.device_lab.owner_waike_artifacts import DEVICE_LAB_HUB_ENDPOINT_POLICY_V1


def test_build_usernet_restrict_on_without_guestfwd():
    """1. No guest services => existing restrict=on usernet unchanged."""
    net = build_usernet_netdev(restrict=True, rules=())
    assert net == "user,id=n0,restrict=on"
    assert "guestfwd" not in net


def test_build_usernet_unrestricted_not_default_pass_shape():
    net = build_usernet_netdev(restrict=False, rules=())
    assert net == "user,id=n0"
    assert "restrict=on" not in net


def test_one_valid_guest_service_forward_emits_guestfwd():
    """2. One valid GuestServiceForward => expected guestfwd emitted."""
    c = guestfwd_proof_service_forward()
    d = c.to_dict()
    assert d["restrict"] is True
    assert "guestfwd=tcp:10.0.2.100:18787-tcp:127.0.0.1:18787" in d["qemu_netdev"]
    assert d["qemu_netdev"].startswith("user,id=n0,restrict=on,")


def test_device_lab_hub_httpd_forward_contract():
    c = device_lab_hub_httpd_forward()
    d = c.to_dict()
    assert d["schema"] == "gunnchos.device_lab.guest_service_forward.v1"
    assert d["restrict"] is True
    assert "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787" in d["qemu_netdev"]
    assert "guestfwd=tcp:10.0.2.100:8767-tcp:127.0.0.1:8767" in d["qemu_netdev"]
    assert d["qemu_netdev"].startswith("user,id=n0,restrict=on,")


def test_invalid_guest_ip_rejected():
    """3. Invalid guest IP rejected."""
    with pytest.raises(GuestServiceForwardError, match="guest_ip_outside_qemu_usernet"):
        validate_guest_forward_rule(
            GuestForwardRule(
                name="bad",
                guest_addr="192.168.1.10",
                guest_port=8787,
                host_addr="127.0.0.1",
                host_port=8787,
            )
        )
    with pytest.raises(GuestServiceForwardError, match="guest_ip_reserved"):
        validate_guest_forward_rule(
            GuestForwardRule(
                name="gw",
                guest_addr="10.0.2.2",
                guest_port=8787,
                host_addr="127.0.0.1",
                host_port=8787,
            )
        )


def test_non_loopback_host_rejected_by_default():
    """4. Non-loopback host target rejected by default."""
    with pytest.raises(GuestServiceForwardError, match="non_loopback_host_rejected"):
        validate_guest_forward_rule(
            GuestForwardRule(
                name="ext",
                guest_addr="10.0.2.100",
                guest_port=8787,
                host_addr="8.8.8.8",
                host_port=8787,
            )
        )


def test_duplicate_guest_endpoint_rejected():
    """5. Duplicate guest endpoint rejected."""
    r1 = GuestForwardRule(
        name="a",
        guest_addr="10.0.2.100",
        guest_port=8787,
        host_addr="127.0.0.1",
        host_port=8787,
    )
    r2 = GuestForwardRule(
        name="b",
        guest_addr="10.0.2.100",
        guest_port=8787,
        host_addr="127.0.0.1",
        host_port=9999,
    )
    with pytest.raises(GuestServiceForwardError, match="duplicate_guest_endpoint"):
        validate_guest_forward_rules((r1, r2))


def test_unrestricted_networking_not_required_for_guestfwd_pass():
    """6. Unrestricted networking is not required for guestfwd PASS."""
    net = build_usernet_netdev(
        restrict=True,
        rules=(
            GuestForwardRule(
                name="hub",
                guest_addr="10.0.2.100",
                guest_port=8787,
                host_addr="127.0.0.1",
                host_port=8787,
            ),
        ),
    )
    assert "restrict=on" in net
    assert "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787" in net
    # Explicit: guestfwd coexists with restrict; unrestricted shape is not needed.
    assert not net.startswith("user,id=n0,guestfwd")


def test_policy_fixture_matches_guestfwd_url():
    """7. WAIKE policy fixture matches guest-visible forwarded URL."""
    assert DEVICE_LAB_HUB_ENDPOINT_POLICY_V1["authorized_hub_base_url"] == "http://10.0.2.100:8787"
    assert DEVICE_LAB_HUB_ENDPOINT_POLICY_V1["allow_insecure_local"] is True


def test_apply_env_sets_restrict_and_guestfwd(monkeypatch):
    c = device_lab_hub_httpd_forward()
    apply_guest_service_forward_env(c)
    assert os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] == "1"
    assert os.environ["GUNNCHDEVICE_LAB_INTERACTIVE_NET"] == "1"
    rules = json.loads(os.environ["GUNNCHDEVICE_LAB_GUESTFWD"])
    assert rules[0]["guest_addr"] == "10.0.2.100"
    netdev, meta = resolve_boot_usernet_netdev()
    assert meta["restrict"] is True
    assert meta["unrestricted_usernet"] is False
    assert "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787" in netdev


def test_parse_guestfwd_semicolon_clause():
    rules = parse_guestfwd_env(
        "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787"
    )
    assert len(rules) == 1
    assert rules[0].guest_port == 8787
    assert rules[0].host_addr == "127.0.0.1"


def test_parse_guestfwd_rejects_garbage():
    with pytest.raises((GuestServiceForwardError, ValueError)):
        parse_guestfwd_env("not-a-rule")


def test_guest_forward_rule_clause():
    r = GuestForwardRule(
        name="hub",
        guest_addr="10.0.2.100",
        guest_port=8787,
        host_addr="127.0.0.1",
        host_port=8787,
    )
    assert r.qemu_guestfwd_clause() == "guestfwd=tcp:10.0.2.100:8787-tcp:127.0.0.1:8787"
    assert r.guest_base_url() == "http://10.0.2.100:8787"
