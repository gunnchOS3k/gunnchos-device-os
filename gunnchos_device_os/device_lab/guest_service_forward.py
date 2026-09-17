"""GuestServiceForward v1 — scoped QEMU usernet guest→host TCP forwards.

Keeps Interactive Guest isolation (`restrict=on`) while allowing an explicit
allowlist of guest-visible addresses to reach host loopback services
(Device Lab Hub, owner artifact httpd, deterministic network proofs).
Never implies unrestricted usernet.
"""
from __future__ import annotations

import ipaddress
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCHEMA = "gunnchos.device_lab.guest_service_forward.v1"
DEFAULT_GUEST_HUB_ADDR = "10.0.2.100"
DEFAULT_HUB_PORT = 8787
DEFAULT_HTTPD_PORT = 8767
DEFAULT_HOST_LOOPBACK = "127.0.0.1"
# QEMU user-mode networking default subnet (slirp): 10.0.2.0/24
QEMU_USERNET_SUBNET = ipaddress.ip_network("10.0.2.0/24")


class GuestServiceForwardError(ValueError):
    """Fail-closed validation error for GuestServiceForward rules."""


@dataclass(frozen=True)
class GuestForwardRule:
    """One guestfwd rule: guest sees guest_addr:guest_port → host_addr:host_port.

    Optional ``cmd`` selects QEMU ``guestfwd=...-cmd:...`` (per-connection
    stdin/stdout relay) instead of ``-tcp:HADDR:HPORT``. Prefer cmd for Hub
    HTTP when tcp-to-tcp guestfwd drops OPTIONS/POST payloads.
    """

    name: str
    guest_addr: str
    guest_port: int
    host_addr: str
    host_port: int
    protocol: str = "tcp"
    cmd: str | None = None

    def qemu_guestfwd_clause(self) -> str:
        # QEMU usernet: guestfwd=tcp:GADDR:GPORT-tcp:HADDR:HPORT
        # or guestfwd=tcp:GADDR:GPORT-cmd:COMMAND (no commas in COMMAND).
        proto = self.protocol.lower()
        left = f"guestfwd={proto}:{self.guest_addr}:{int(self.guest_port)}"
        if self.cmd:
            cmd = self.cmd.strip()
            if not cmd or "," in cmd:
                raise GuestServiceForwardError(
                    f"invalid_guestfwd_cmd:{cmd!r}"
                )
            return f"{left}-cmd:{cmd}"
        return f"{left}-{proto}:{self.host_addr}:{int(self.host_port)}"

    def guest_base_url(self, *, scheme: str = "http") -> str:
        return f"{scheme}://{self.guest_addr}:{int(self.guest_port)}"

    def guest_endpoint_key(self) -> tuple[str, str, int]:
        return (self.protocol.lower(), self.guest_addr, int(self.guest_port))


@dataclass(frozen=True)
class GuestServiceForwardV1:
    schema: str
    restrict: bool
    rules: tuple[GuestForwardRule, ...]
    notes: str = (
        "restrict=on isolation; explicit guestfwd only; Hub/httpd bind host loopback."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "restrict": self.restrict,
            "rules": [asdict(r) for r in self.rules],
            "notes": self.notes,
            "qemu_netdev": build_usernet_netdev(restrict=self.restrict, rules=self.rules),
        }

    def qemu_netdev(self) -> str:
        return build_usernet_netdev(restrict=self.restrict, rules=self.rules)


def _validate_port(port: int, *, label: str) -> int:
    p = int(port)
    if p < 1 or p > 65535:
        raise GuestServiceForwardError(f"invalid_{label}_port:{p}")
    return p


def validate_guest_forward_rule(
    rule: GuestForwardRule,
    *,
    allow_non_loopback_host: bool = False,
) -> GuestForwardRule:
    """Validate one rule. TCP-only; guest IP in QEMU usernet; host loopback by default."""
    proto = (rule.protocol or "tcp").lower()
    if proto != "tcp":
        raise GuestServiceForwardError(f"unsupported_protocol:{proto}")
    try:
        guest_ip = ipaddress.ip_address(rule.guest_addr)
    except ValueError as exc:
        raise GuestServiceForwardError(f"invalid_guest_ip:{rule.guest_addr}") from exc
    if guest_ip not in QEMU_USERNET_SUBNET:
        raise GuestServiceForwardError(
            f"guest_ip_outside_qemu_usernet:{rule.guest_addr}"
        )
    # Guest service IP must not collide with gateway / DNS / DHCP reserved hosts.
    reserved = {
        ipaddress.ip_address("10.0.2.0"),
        ipaddress.ip_address("10.0.2.2"),  # gateway
        ipaddress.ip_address("10.0.2.3"),  # DNS
        ipaddress.ip_address("10.0.2.255"),
    }
    if guest_ip in reserved:
        raise GuestServiceForwardError(f"guest_ip_reserved:{rule.guest_addr}")
    try:
        host_ip = ipaddress.ip_address(rule.host_addr)
    except ValueError as exc:
        raise GuestServiceForwardError(f"invalid_host_ip:{rule.host_addr}") from exc
    if not allow_non_loopback_host and not host_ip.is_loopback:
        raise GuestServiceForwardError(
            f"non_loopback_host_rejected:{rule.host_addr}"
        )
    guest_port = _validate_port(rule.guest_port, label="guest")
    host_port = _validate_port(rule.host_port, label="host")
    cmd = (rule.cmd or None) and str(rule.cmd).strip() or None
    if cmd and "," in cmd:
        raise GuestServiceForwardError(f"invalid_guestfwd_cmd_comma:{cmd!r}")
    return GuestForwardRule(
        name=rule.name,
        guest_addr=str(guest_ip),
        guest_port=guest_port,
        host_addr=str(host_ip),
        host_port=host_port,
        protocol=proto,
        cmd=cmd,
    )


def validate_guest_forward_rules(
    rules: tuple[GuestForwardRule, ...] | list[GuestForwardRule],
    *,
    allow_non_loopback_host: bool = False,
) -> tuple[GuestForwardRule, ...]:
    seen: set[tuple[str, str, int]] = set()
    out: list[GuestForwardRule] = []
    for raw in rules:
        rule = validate_guest_forward_rule(
            raw, allow_non_loopback_host=allow_non_loopback_host
        )
        key = rule.guest_endpoint_key()
        if key in seen:
            raise GuestServiceForwardError(
                f"duplicate_guest_endpoint:{key[0]}:{key[1]}:{key[2]}"
            )
        seen.add(key)
        out.append(rule)
    return tuple(out)


def hub_guestfwd_cmd_relay_command(
    *,
    host_addr: str = DEFAULT_HOST_LOOPBACK,
    host_port: int = DEFAULT_HUB_PORT,
    python_bin: str | None = None,
) -> str:
    """Build comma-free QEMU ``-cmd:`` string for Hub guestfwd relay.

    Prefer a no-space wrapper script path (QEMU netdev parsing is comma-split
    and some builds are fragile with argv spaces). Fall back to explicit
    ``python relay.py host port`` when the wrapper is absent or port differs.
    """
    here = Path(__file__).resolve().parent
    wrapper = here / f"hub_guestfwd_cmd_relay_{int(host_port)}.sh"
    if (
        wrapper.is_file()
        and host_addr == DEFAULT_HOST_LOOPBACK
        and int(host_port) == DEFAULT_HUB_PORT
    ):
        # Ensure executable bit for QEMU cmd spawn.
        try:
            mode = wrapper.stat().st_mode
            if not (mode & 0o111):
                wrapper.chmod(mode | 0o755)
        except OSError:
            pass
        cmd = str(wrapper)
        if "," in cmd:
            raise GuestServiceForwardError(f"invalid_guestfwd_cmd_comma:{cmd!r}")
        return cmd

    relay = here / "hub_guestfwd_cmd_relay.py"
    py = python_bin or os.environ.get("GUNNCHDEVICE_LAB_GUESTFWD_PYTHON") or sys.executable
    if not python_bin:
        for candidate in ("/usr/bin/python3", "/opt/homebrew/bin/python3"):
            if Path(candidate).is_file():
                py = candidate
                break
    cmd = f"{py} {relay} {host_addr} {int(host_port)}"
    if "," in cmd:
        raise GuestServiceForwardError(f"invalid_guestfwd_cmd_comma:{cmd!r}")
    return cmd

def device_lab_hub_only_forward(
    *,
    hub_port: int = DEFAULT_HUB_PORT,
    guest_addr: str = DEFAULT_GUEST_HUB_ADDR,
    host_addr: str = DEFAULT_HOST_LOOPBACK,
    restrict: bool = True,
    use_cmd_relay: bool | None = None,
) -> GuestServiceForwardV1:
    """Hub-only scoped forward (host must listen on hub_port before QEMU starts).

    Default: QEMU ``-cmd:`` per-connection relay into host Hub/CORS proxy.
    Set ``use_cmd_relay=False`` or env ``GUNNCHDEVICE_LAB_GUESTFWD_TCP=1`` to
    force legacy ``-tcp:`` guestfwd.
    """
    if use_cmd_relay is None:
        use_cmd_relay = os.environ.get("GUNNCHDEVICE_LAB_GUESTFWD_TCP", "").strip() not in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }
    cmd = (
        hub_guestfwd_cmd_relay_command(host_addr=host_addr, host_port=hub_port)
        if use_cmd_relay
        else None
    )
    rules = validate_guest_forward_rules(
        (
            GuestForwardRule(
                name="device_lab_hub",
                guest_addr=guest_addr,
                guest_port=hub_port,
                host_addr=host_addr,
                host_port=hub_port,
                cmd=cmd,
            ),
        )
    )
    return GuestServiceForwardV1(schema=SCHEMA, restrict=restrict, rules=rules)


def device_lab_hub_httpd_forward(
    *,
    hub_port: int = DEFAULT_HUB_PORT,
    httpd_port: int = DEFAULT_HTTPD_PORT,
    guest_addr: str = DEFAULT_GUEST_HUB_ADDR,
    host_addr: str = DEFAULT_HOST_LOOPBACK,
    restrict: bool = True,
    use_cmd_relay: bool | None = None,
) -> GuestServiceForwardV1:
    """Canonical Device Lab Hub + owner httpd scoped forward contract.

    IMPORTANT: QEMU usernet guestfwd connects to host ports at VM start.
    Both hub_port and httpd_port must already be listening on host_addr or
    QEMU fails with "Could not open guest forwarding device".
    """
    if use_cmd_relay is None:
        use_cmd_relay = os.environ.get("GUNNCHDEVICE_LAB_GUESTFWD_TCP", "").strip() not in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }
    hub_cmd = (
        hub_guestfwd_cmd_relay_command(host_addr=host_addr, host_port=hub_port)
        if use_cmd_relay
        else None
    )
    rules = validate_guest_forward_rules(
        (
            GuestForwardRule(
                name="device_lab_hub",
                guest_addr=guest_addr,
                guest_port=hub_port,
                host_addr=host_addr,
                host_port=hub_port,
                cmd=hub_cmd,
            ),
            GuestForwardRule(
                name="owner_artifact_httpd",
                guest_addr=guest_addr,
                guest_port=httpd_port,
                host_addr=host_addr,
                host_port=httpd_port,
            ),
        )
    )
    return GuestServiceForwardV1(
        schema=SCHEMA,
        restrict=restrict,
        rules=rules,
    )


def guestfwd_proof_service_forward(
    *,
    guest_port: int = 18787,
    host_port: int = 18787,
    guest_addr: str = DEFAULT_GUEST_HUB_ADDR,
    host_addr: str = DEFAULT_HOST_LOOPBACK,
    restrict: bool = True,
) -> GuestServiceForwardV1:
    """Deterministic network-proof forward for 17G.5C1 (temp test service)."""
    rules = validate_guest_forward_rules(
        (
            GuestForwardRule(
                name="guestfwd_test_service",
                guest_addr=guest_addr,
                guest_port=guest_port,
                host_addr=host_addr,
                host_port=host_port,
            ),
        )
    )
    return GuestServiceForwardV1(schema=SCHEMA, restrict=restrict, rules=rules)


def build_usernet_netdev(
    *,
    restrict: bool = True,
    rules: tuple[GuestForwardRule, ...] | list[GuestForwardRule] = (),
    validate: bool = True,
    allow_non_loopback_host: bool = False,
) -> str:
    """Assemble QEMU `-netdev user,...` value (type + id + optional restrict/guestfwd)."""
    parts: list[str] = ["user", "id=n0"]
    if restrict:
        parts.append("restrict=on")
    validated = (
        validate_guest_forward_rules(
            rules, allow_non_loopback_host=allow_non_loopback_host
        )
        if validate and rules
        else tuple(rules)
    )
    for rule in validated:
        parts.append(rule.qemu_guestfwd_clause())
    return ",".join(parts)


def parse_guestfwd_env(raw: str | None = None) -> list[GuestForwardRule]:
    """Parse GUNNCHDEVICE_LAB_GUESTFWD JSON array or semicolon guestfwd clauses."""
    text = (raw if raw is not None else os.environ.get("GUNNCHDEVICE_LAB_GUESTFWD") or "").strip()
    if not text:
        return []
    if text.startswith("["):
        data = json.loads(text)
        out: list[GuestForwardRule] = []
        for i, item in enumerate(data):
            cmd_raw = item.get("cmd")
            cmd = str(cmd_raw).strip() if cmd_raw else None
            out.append(
                GuestForwardRule(
                    name=str(item.get("name") or f"fwd{i}"),
                    guest_addr=str(item["guest_addr"]),
                    guest_port=int(item["guest_port"]),
                    host_addr=str(item.get("host_addr") or DEFAULT_HOST_LOOPBACK),
                    host_port=int(item.get("host_port") or item["guest_port"]),
                    protocol=str(item.get("protocol") or "tcp"),
                    cmd=cmd or None,
                )
            )
        return list(validate_guest_forward_rules(out))
    # Semicolon-separated full guestfwd= clauses or bare tcp:...-tcp:... / -cmd:... forms.
    rules: list[GuestForwardRule] = []
    for i, chunk in enumerate(text.split(";")):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith("guestfwd="):
            chunk = chunk[len("guestfwd=") :]
        # tcp:10.0.2.100:8787-tcp:127.0.0.1:8787
        # tcp:10.0.2.100:8787-cmd:/path/to/relay
        if not chunk.startswith("tcp:"):
            raise GuestServiceForwardError(f"invalid_guestfwd_clause:{chunk}")
        if "-cmd:" in chunk:
            left, cmd = chunk.split("-cmd:", 1)
            g_parts = left.split(":")
            if len(g_parts) != 3 or not cmd.strip():
                raise GuestServiceForwardError(f"invalid_guestfwd_clause:{chunk}")
            # Host addr/port are informational when cmd is set; default loopback:guest_port.
            rules.append(
                GuestForwardRule(
                    name=f"env{i}",
                    guest_addr=g_parts[1],
                    guest_port=int(g_parts[2]),
                    host_addr=DEFAULT_HOST_LOOPBACK,
                    host_port=int(g_parts[2]),
                    cmd=cmd.strip(),
                )
            )
            continue
        if "-tcp:" not in chunk:
            raise GuestServiceForwardError(f"invalid_guestfwd_clause:{chunk}")
        left, right = chunk.split("-tcp:", 1)
        g_parts = left.split(":")
        h_parts = right.split(":")
        # left: tcp:GADDR:GPORT ; right after -tcp: is HADDR:HPORT
        if len(g_parts) != 3 or len(h_parts) != 2:
            raise GuestServiceForwardError(f"invalid_guestfwd_clause:{chunk}")
        rules.append(
            GuestForwardRule(
                name=f"env{i}",
                guest_addr=g_parts[1],
                guest_port=int(g_parts[2]),
                host_addr=h_parts[0],
                host_port=int(h_parts[1]),
            )
        )
    return list(validate_guest_forward_rules(rules))


def apply_guest_service_forward_env(contract: GuestServiceForwardV1) -> None:
    """Export contract into QEMU boot env (restrict + guestfwd JSON)."""
    os.environ["GUNNCHDEVICE_LAB_INTERACTIVE_NET"] = "1"
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "1" if contract.restrict else "0"
    os.environ["GUNNCHDEVICE_LAB_GUESTFWD"] = json.dumps(
        [asdict(r) for r in contract.rules], separators=(",", ":")
    )
    os.environ["GUNNCHDEVICE_LAB_GUEST_SERVICE_FORWARD_SCHEMA"] = contract.schema


def clear_guest_service_forward_env() -> None:
    """Reset guestfwd env so default boot is restrict=on with no forwards."""
    os.environ["GUNNCHDEVICE_LAB_INTERACTIVE_NET"] = "1"
    os.environ["GUNNCHDEVICE_LAB_NET_RESTRICT"] = "1"
    os.environ.pop("GUNNCHDEVICE_LAB_GUESTFWD", None)
    os.environ.pop("GUNNCHDEVICE_LAB_GUEST_SERVICE_FORWARD_SCHEMA", None)


def resolve_boot_usernet_netdev() -> tuple[str, dict[str, Any]]:
    """Resolve netdev string + metadata from env (used by qemu_guest)."""
    restrict = os.environ.get("GUNNCHDEVICE_LAB_NET_RESTRICT", "1").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    rules = parse_guestfwd_env()
    netdev = build_usernet_netdev(restrict=restrict, rules=rules)
    meta = {
        "restrict": restrict,
        "guestfwd_rule_count": len(rules),
        "rules": [asdict(r) for r in rules],
        "netdev": netdev,
        "unrestricted_usernet": not restrict,
        "schema": SCHEMA,
    }
    return netdev, meta
