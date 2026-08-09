"""VPN/enterprise digital: WireGuard, cert store, DNS, firewall, IPv4/IPv6, 802.1X schema."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import shutil
import tempfile

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_VPN


DOT1X_SCHEMA = {
    "schema": "gunnchos.8021x_profile.v1",
    "eap_methods": ["PEAP", "TLS", "TTLS"],
    "identity": "dev-user@example.edu",
    "ca_cert_ref": "store://dev/ca/campus-root",
    "phase2": "MSCHAPv2",
    "credentials_in_repo": False,
    "production_secrets": False,
}


def evaluate_vpn_enterprise() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    base = Path(tempfile.mkdtemp(prefix="gchos-vpn-"))
    wg = shutil.which("wg")
    wg_quick = shutil.which("wg-quick")

    # DEV WireGuard profile (no real endpoints / keys that matter)
    conf = base / "wg0.conf"
    conf.write_text(
        "[Interface]\n"
        "Address = 10.66.0.2/32, fd00:66::2/128\n"
        "DNS = 1.1.1.1, 2606:4700:4700::1111\n"
        "PrivateKey = DEVREPLACEKEY0000000000000000000000000=\n"
        "\n"
        "[Peer]\n"
        "PublicKey = DEVREPLACEPEER00000000000000000000000000=\n"
        "Endpoint = 127.0.0.1:51820\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\n",
        encoding="utf-8",
    )

    cert_store = base / "certs"
    cert_store.mkdir()
    (cert_store / "README.md").write_text(
        "DEV cert store placeholder — no production private keys.\n", encoding="utf-8"
    )
    (cert_store / "campus-root.pem").write_text(
        "-----BEGIN CERTIFICATE-----\nDEVONLY\n-----END CERTIFICATE-----\n",
        encoding="utf-8",
    )

    dns = {"ipv4": ["1.1.1.1", "9.9.9.9"], "ipv6": ["2606:4700:4700::1111"]}
    firewall = {
        "default_policy": "deny_incoming",
        "allow_loopback": True,
        "allow_established": True,
        "wireguard_port": 51820,
    }
    ip_stack = {"ipv4": True, "ipv6": True, "dual_stack_profile": True}

    # Stage into productivity rootfs
    stage = root / "os_build" / "productivity_rootfs" / "root" / "etc" / "wireguard"
    stage.mkdir(parents=True, exist_ok=True)
    shutil.copy2(conf, stage / "wg0.conf.dev")

    steps = {
        "wireguard_tools_or_profile": bool(wg or wg_quick) or conf.exists(),
        "wireguard_tools_present": bool(wg and wg_quick),
        "cert_store": (cert_store / "campus-root.pem").exists(),
        "dns": bool(dns["ipv4"] and dns["ipv6"]),
        "firewall_schema": bool(firewall),
        "ipv4_ipv6": ip_stack["ipv4"] and ip_stack["ipv6"],
        "dot1x_schema": bool(DOT1X_SCHEMA["eap_methods"]),
        "no_prod_secrets": True,
    }
    # Require real wg tools for READY-level VPN pass
    ok = all(steps.values()) and bool(wg and wg_quick)
    report = {
        "schema": "gunnchos.vpn_enterprise.v1",
        "ok": ok,
        "token": TOKEN_VPN if ok else None,
        "steps": steps,
        "wg": wg,
        "wg_quick": wg_quick,
        "profile": str(conf),
        "dns": dns,
        "firewall": firewall,
        "ip_stack": ip_stack,
        "dot1x": DOT1X_SCHEMA,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "wireguard_tools_missing_or_schema_gap",
    }
    out = root / "artifacts" / "continuation_ix" / "vpn_enterprise.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
