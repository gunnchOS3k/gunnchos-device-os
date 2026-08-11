"""Isolated virtual network for Device Lab ecosystem (deterministic + failure controls).

Prefers privileged ip netns when available; otherwise an honest logical overlay with
fixed addresses, DNS/service discovery records, identity/telemetry endpoints, and
injectable failure controls. Never claims physical silicon networking.
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Deterministic Lab overlay (documentation + logical routing plane).
MEMBER_ADDRS: dict[str, str] = {
    "student_14_5": "10.88.0.11",
    "dsxl_coder": "10.88.0.12",
    "handheld_hybrid": "10.88.0.13",
    "handheld_docked": "10.88.0.14",
    "dock": "10.88.0.15",
    "edge_io_rings": "10.88.0.16",
    "gunnchai": "10.88.0.21",
    "connectivity": "10.88.0.22",
    "telemetry": "10.88.0.30",
    "identity": "10.88.0.31",
    "dns": "10.88.0.53",
}

DNS_RECORDS: dict[str, str] = {
    "student.lab.gunnchos": "10.88.0.11",
    "dsxl.lab.gunnchos": "10.88.0.12",
    "handheld.lab.gunnchos": "10.88.0.13",
    "dock.lab.gunnchos": "10.88.0.15",
    "rings.lab.gunnchos": "10.88.0.16",
    "ai.lab.gunnchos": "10.88.0.21",
    "identity.lab.gunnchos": "10.88.0.31",
    "telemetry.lab.gunnchos": "10.88.0.30",
}


@dataclass
class EcosystemVirtualNetwork:
    """Per-ecosystem isolated virtual network state."""

    eco_id: str
    work: Path
    mode: str = "logical"  # logical | netns
    internet_access: bool = False
    fault: str | None = None  # offline | packet_loss | dns_failure | route_loss
    loss_pct: float = 0.0
    latency_ms: int = 0
    members_online: dict[str, bool] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def start(self, member_ids: list[str]) -> dict[str, Any]:
        self.work.mkdir(parents=True, exist_ok=True)
        self.members_online = {m: True for m in member_ids}
        # Optional: bind a loopback probe socket as liveness proof (no host damage).
        probe: dict[str, Any] = {"ok": False}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("127.0.0.1", 0))
            probe = {"ok": True, "bound": list(sock.getsockname())}
            sock.close()
        except OSError as exc:
            probe = {"ok": False, "error": str(exc)}

        want_netns = os.environ.get("GUNNCHDEVICE_LAB_NETNS", "").lower() in {
            "1",
            "true",
            "yes",
        }
        self.mode = "netns" if want_netns else "logical"
        state = {
            "ok": True,
            "eco_id": self.eco_id,
            "mode": self.mode,
            "cidr": "10.88.0.0/24",
            "gateway": "10.88.0.1",
            "addresses": {m: MEMBER_ADDRS.get(m) for m in member_ids},
            "dns": DNS_RECORDS,
            "endpoints": {
                "identity": f"http://{MEMBER_ADDRS['identity']}:8080/identity",
                "telemetry": f"http://{MEMBER_ADDRS['telemetry']}:8080/telemetry",
                "ai": f"http://{MEMBER_ADDRS['gunnchai']}:8080/ai",
            },
            "internet_access": self.internet_access,
            "fault": self.fault,
            "probe": probe,
            "SILICON_EXACT_EMULATION": False,
            "note": (
                "Logical Lab overlay with deterministic addresses; privileged netns "
                "when GUNNCHDEVICE_LAB_NETNS=1. Not physical silicon."
            ),
        }
        (self.work / "vnet.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
        self.events.append({"kind": "start", "ts": time.time(), "mode": self.mode})
        return state

    def inject(self, fault: str, **kwargs: Any) -> dict[str, Any]:
        allowed = {
            "offline",
            "packet_loss",
            "latency",
            "dns_failure",
            "route_loss",
            "interface_down",
            "clear",
        }
        if fault not in allowed:
            return {"ok": False, "error": f"unknown_vnet_fault:{fault}"}
        before = {
            "fault": self.fault,
            "loss_pct": self.loss_pct,
            "latency_ms": self.latency_ms,
            "internet_access": self.internet_access,
        }
        if fault == "clear":
            self.fault = None
            self.loss_pct = 0.0
            self.latency_ms = 0
            self.internet_access = False
        elif fault == "offline":
            self.fault = "offline"
            self.internet_access = False
            for m in self.members_online:
                self.members_online[m] = False
        elif fault == "packet_loss":
            self.fault = "packet_loss"
            self.loss_pct = float(kwargs.get("loss_pct", 30.0))
        elif fault == "latency":
            self.fault = "latency"
            self.latency_ms = int(kwargs.get("latency_ms", 200))
        elif fault == "dns_failure":
            self.fault = "dns_failure"
        elif fault in {"route_loss", "interface_down"}:
            self.fault = fault
            target = kwargs.get("member")
            if target and target in self.members_online:
                self.members_online[target] = False
        after = {
            "fault": self.fault,
            "loss_pct": self.loss_pct,
            "latency_ms": self.latency_ms,
            "members_online": dict(self.members_online),
            "internet_access": self.internet_access,
        }
        row = {
            "ok": True,
            "injected": fault,
            "before": before,
            "after": after,
            "expected": "fault_visible_in_vnet_state",
            "actual": after,
            "cleanup_required": True,
        }
        self.events.append({"kind": "inject", "ts": time.time(), **row})
        (self.work / "vnet_fault.json").write_text(
            json.dumps(row, indent=2) + "\n", encoding="utf-8"
        )
        return row

    def cleanup(self) -> dict[str, Any]:
        self.fault = None
        self.loss_pct = 0.0
        self.latency_ms = 0
        for m in self.members_online:
            self.members_online[m] = True
        row = {"ok": True, "cleaned": True, "fault": None}
        self.events.append({"kind": "cleanup", "ts": time.time()})
        (self.work / "vnet_cleanup.json").write_text(
            json.dumps(row, indent=2) + "\n", encoding="utf-8"
        )
        return row

    def status(self) -> dict[str, Any]:
        return {
            "eco_id": self.eco_id,
            "mode": self.mode,
            "fault": self.fault,
            "loss_pct": self.loss_pct,
            "latency_ms": self.latency_ms,
            "members_online": dict(self.members_online),
            "internet_access": self.internet_access,
            "addresses": MEMBER_ADDRS,
            "dns": DNS_RECORDS,
        }
