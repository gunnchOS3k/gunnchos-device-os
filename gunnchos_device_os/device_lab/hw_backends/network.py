"""Network backend — privileged netns/veth with real packet transfer; logical fallback."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


@dataclass
class NetworkBackend:
    state: str = "online"
    ethernet_via_dock: bool = False
    loss_pct: float = 0.0
    latency_ms: int = 0
    mode: str = "logical"  # logical | netns
    ns_name: str | None = None
    host_if: str | None = None
    peer_if: str | None = None
    host_addr: str | None = None
    peer_addr: str | None = None
    packet_transfer: dict[str, Any] | None = None
    e4_reference_proof: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)

    def start(self) -> dict[str, Any]:
        ip = shutil.which("ip")
        want_netns = _env_truthy("GUNNCHDEVICE_LAB_NETNS") or _env_truthy(
            "GUNNCHDEVICE_LAB_PRIVILEGED_NET"
        )
        if want_netns and ip and os.geteuid() == 0:
            self.ns_name = "gchos-lab0"
            self.host_if = "gchos-veth0"
            self.peer_if = "gchos-veth1"
            self.host_addr = "10.67.0.1"
            self.peer_addr = "10.67.0.2"
            # Clean any leftover namespace/ifaces from a prior crashed run.
            self._force_cleanup(ip)
            add = _run([ip, "netns", "add", self.ns_name])
            if add.returncode != 0 and "File exists" not in (add.stderr or ""):
                self.mode = "logical"
                self.e4_reference_proof = False
                self.events.append(
                    {
                        "kind": "start",
                        "mode": self.mode,
                        "error": (add.stderr or add.stdout or "").strip(),
                    }
                )
            else:
                self.mode = "netns"
                self.e4_reference_proof = False  # earned only after packet transfer
        else:
            self.mode = "logical"
            self.e4_reference_proof = False
        self.state = "online"
        self.events.append({"kind": "start", "mode": self.mode})
        return {
            "ok": True,
            "mode": self.mode,
            "state": self.state,
            "e4_reference_proof": self.e4_reference_proof,
            "note": (
                "Privileged ip netns+veth with actual packet transfer when root and "
                "GUNNCHDEVICE_LAB_NETNS=1 (or GUNNCHDEVICE_LAB_PRIVILEGED_NET=1); "
                "otherwise logical FALLBACK_ONLY / NOT_E4_REFERENCE_PROOF."
            ),
        }

    def _force_cleanup(self, ip: str) -> None:
        if self.host_if:
            _run([ip, "link", "del", self.host_if])
        if self.ns_name:
            _run([ip, "netns", "del", self.ns_name])

    def _netns_attach(self) -> dict[str, Any]:
        assert self.ns_name and self.host_if and self.peer_if
        assert self.host_addr and self.peer_addr
        ip = shutil.which("ip")
        if not ip:
            return {"ok": False, "error": "ip_not_found", "mode": "logical"}

        steps: list[dict[str, Any]] = []

        def step(label: str, cmd: list[str]) -> bool:
            r = _run(cmd)
            steps.append(
                {
                    "step": label,
                    "cmd": cmd,
                    "rc": r.returncode,
                    "stderr": (r.stderr or "").strip()[:400],
                }
            )
            return r.returncode == 0

        ok = True
        ok = step("veth_add", [ip, "link", "add", self.host_if, "type", "veth", "peer", "name", self.peer_if]) and ok
        ok = step("peer_to_ns", [ip, "link", "set", self.peer_if, "netns", self.ns_name]) and ok
        ok = step(
            "host_addr",
            [ip, "addr", "add", f"{self.host_addr}/24", "dev", self.host_if],
        ) and ok
        ok = step("host_up", [ip, "link", "set", self.host_if, "up"]) and ok
        ok = step(
            "peer_addr",
            [
                ip,
                "netns",
                "exec",
                self.ns_name,
                ip,
                "addr",
                "add",
                f"{self.peer_addr}/24",
                "dev",
                self.peer_if,
            ],
        ) and ok
        ok = step(
            "peer_up",
            [ip, "netns", "exec", self.ns_name, ip, "link", "set", self.peer_if, "up"],
        ) and ok
        ok = step(
            "peer_lo",
            [ip, "netns", "exec", self.ns_name, ip, "link", "set", "lo", "up"],
        ) and ok
        ok = step(
            "peer_route",
            [
                ip,
                "netns",
                "exec",
                self.ns_name,
                ip,
                "route",
                "add",
                "default",
                "via",
                self.host_addr,
            ],
        ) and ok

        # Prove interface visibility inside the namespace.
        link_show = _run([ip, "netns", "exec", self.ns_name, ip, "link", "show", self.peer_if])
        iface_visible = link_show.returncode == 0 and self.peer_if in (link_show.stdout or "")
        steps.append(
            {
                "step": "iface_visible_in_ns",
                "ok": iface_visible,
                "stdout": (link_show.stdout or "")[:400],
            }
        )

        packet = self._packet_transfer_probe(ip)
        steps.append({"step": "packet_transfer", **packet})
        self.packet_transfer = packet
        self.e4_reference_proof = bool(ok and iface_visible and packet.get("ok"))
        self.ethernet_via_dock = self.e4_reference_proof
        self.state = "online_ethernet_dock" if self.ethernet_via_dock else "online"
        self.events.append(
            {
                "kind": "dock_ethernet_attach",
                "mode": self.mode,
                "e4_reference_proof": self.e4_reference_proof,
                "steps": steps,
            }
        )
        return {
            "ok": self.e4_reference_proof,
            "ethernet_via_dock": self.ethernet_via_dock,
            "state": self.state,
            "mode": self.mode,
            "ns_name": self.ns_name,
            "host_if": self.host_if,
            "peer_if": self.peer_if,
            "host_addr": self.host_addr,
            "peer_addr": self.peer_addr,
            "packet_transfer": packet,
            "e4_reference_proof": self.e4_reference_proof,
            "steps": steps,
            "NOT_E4_REFERENCE_PROOF": not self.e4_reference_proof,
        }

    def _packet_transfer_probe(self, ip: str) -> dict[str, Any]:
        """Actual packet transfer host ↔ netns (not an in-memory flag)."""
        assert self.ns_name and self.host_addr and self.peer_addr
        # UDP echo: host listens, netns sends a datagram, host receives it.
        payload = b"GUNNCH-LAB-NET-E4"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host_addr, 19670))
        sock.settimeout(2.0)
        try:
            sender = _run(
                [
                    ip,
                    "netns",
                    "exec",
                    self.ns_name,
                    "python3",
                    "-c",
                    (
                        "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); "
                        f"s.sendto({payload!r}, ({self.host_addr!r}, 19670)); s.close()"
                    ),
                ]
            )
            if sender.returncode != 0:
                # Fallback: ICMP ping from ns to host (still real packets).
                ping = _run(
                    [
                        ip,
                        "netns",
                        "exec",
                        self.ns_name,
                        "ping",
                        "-c",
                        "1",
                        "-W",
                        "2",
                        self.host_addr,
                    ]
                )
                return {
                    "ok": ping.returncode == 0,
                    "method": "icmp_ping",
                    "rc": ping.returncode,
                    "stdout": (ping.stdout or "")[:400],
                    "stderr": (ping.stderr or sender.stderr or "")[:400],
                }
            data, addr = sock.recvfrom(256)
            return {
                "ok": data == payload,
                "method": "udp_echo",
                "from": list(addr),
                "bytes": len(data),
                "payload_match": data == payload,
            }
        except (TimeoutError, OSError, socket.timeout) as exc:
            ping = _run(
                [
                    ip,
                    "netns",
                    "exec",
                    self.ns_name,
                    "ping",
                    "-c",
                    "1",
                    "-W",
                    "2",
                    self.host_addr,
                ]
            )
            return {
                "ok": ping.returncode == 0,
                "method": "icmp_ping_after_udp_error",
                "udp_error": str(exc),
                "rc": ping.returncode,
                "stdout": (ping.stdout or "")[:400],
            }
        finally:
            sock.close()

    def dock_ethernet_attach(self) -> dict[str, Any]:
        if self.mode == "netns" and self.ns_name:
            return self._netns_attach()

        # Unprivileged / CI smoke path — honest logical fallback, not E4 reference.
        self.ethernet_via_dock = True
        self.state = "online_ethernet_dock"
        self.e4_reference_proof = False
        self.packet_transfer = {
            "ok": False,
            "method": "logical_in_memory",
            "NOT_E4_REFERENCE_PROOF": True,
        }
        self.events.append(
            {
                "kind": "dock_ethernet_attach",
                "mode": "logical",
                "e4_reference_proof": False,
                "FALLBACK_ONLY": True,
            }
        )
        return {
            "ok": True,
            "ethernet_via_dock": True,
            "state": self.state,
            "mode": "logical",
            "e4_reference_proof": False,
            "FALLBACK_ONLY": True,
            "NOT_E4_REFERENCE_PROOF": True,
            "packet_transfer": self.packet_transfer,
            "note": "Logical in-memory attach only — not E4 G04 reference proof.",
        }

    def dock_ethernet_detach(self) -> dict[str, Any]:
        cleanup = {"ok": True, "cleaned": True}
        if self.mode == "netns":
            cleanup = self.cleanup()
            # Verify interfaces/ns are gone.
            ip = shutil.which("ip")
            gone = True
            details: dict[str, Any] = {}
            if ip and self.host_if:
                show = _run([ip, "link", "show", self.host_if])
                details["host_if_gone"] = show.returncode != 0
                gone = gone and details["host_if_gone"]
            if ip and self.ns_name:
                nss = _run([ip, "netns", "list"])
                details["ns_gone"] = self.ns_name not in (nss.stdout or "")
                gone = gone and details["ns_gone"]
            cleanup["cleanup_verified"] = gone
            cleanup["details"] = details
            if not gone:
                cleanup["ok"] = False

        self.ethernet_via_dock = False
        self.state = "online_wifi" if self.state != "offline" else "offline"
        self.e4_reference_proof = False
        self.events.append({"kind": "dock_ethernet_detach", "cleanup": cleanup})
        return {
            "ok": cleanup.get("ok", True),
            "ethernet_via_dock": False,
            "state": self.state,
            "cleanup": cleanup,
        }

    def apply(self, scenario: str) -> dict[str, Any]:
        mapping = {
            "offline": ("offline", 100.0, 0),
            "bad_wifi": ("degraded", 15.0, 120),
            "packet_loss": ("lossy", 30.0, 40),
            "network_restore": ("online", 0.0, 0),
            "ai_cloud_denied": ("online_cloud_denied", 0.0, 0),
        }
        if scenario not in mapping:
            return {"ok": False, "error": f"unknown_network_scenario:{scenario}"}
        self.state, self.loss_pct, self.latency_ms = mapping[scenario]
        self.events.append({"kind": "scenario", "scenario": scenario, "state": self.state})
        return {
            "ok": True,
            "scenario": scenario,
            "state": self.state,
            "loss_pct": self.loss_pct,
            "latency_ms": self.latency_ms,
            "mode": self.mode,
            "e4_reference_proof": False,
            "note": "apply() scenarios are logical policy overlays, not E4 packet proof.",
        }

    def cleanup(self) -> dict[str, Any]:
        ip = shutil.which("ip")
        if self.mode == "netns" and ip:
            if self.host_if:
                _run([ip, "link", "del", self.host_if])
            if self.ns_name:
                _run([ip, "netns", "del", self.ns_name])
            time.sleep(0.05)
        return {"ok": True, "cleaned": True, "mode": self.mode}
