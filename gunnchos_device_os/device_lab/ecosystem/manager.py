"""Ecosystem topology runtime — start/status/stop/graph with isolated vnet.

Boots member Lab sessions (behavioral / hybrid by default). Simultaneous full soak
(ECO-010) remains PARTIAL until all members + chaos + games lanes are earned.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.ecosystem.topology import MEMBER_PROFILES, ecosystem_topology
from gunnchos_device_os.device_lab.ecosystem.vnet import EcosystemVirtualNetwork
from gunnchos_device_os.device_lab.session import (
    get_session,
    lab_artifact_root,
    list_sessions,
    start_session,
    stop_session,
)


_ECOSYSTEMS: dict[str, "EcosystemRuntime"] = {}

PRIMARY_COMPUTE = (
    "student_14_5",
    "dsxl_coder",
    "handheld_hybrid",
)
# Dock + rings are attached as peripherals / companion profiles (not always full VMs).
PERIPHERAL_MEMBERS = ("dock", "edge_io_rings", "handheld_docked")


@dataclass
class EcosystemRuntime:
    eco_id: str
    repo_root: Path
    work: Path
    preset: str = "full"
    member_instances: dict[str, str] = field(default_factory=dict)
    vnet: EcosystemVirtualNetwork | None = None
    started_at: float = 0.0
    running: bool = False
    state: dict[str, Any] = field(default_factory=dict)

    def start(self, *, members: list[str] | None = None) -> dict[str, Any]:
        self.work.mkdir(parents=True, exist_ok=True)
        topo = ecosystem_topology()
        selected = members or list(PRIMARY_COMPUTE) + ["dock", "edge_io_rings"]
        # Always include primary compute for full preset; peripherals optional.
        if self.preset == "full":
            selected = list(dict.fromkeys(list(PRIMARY_COMPUTE) + list(PERIPHERAL_MEMBERS)))
        elif self.preset == "compute":
            selected = list(PRIMARY_COMPUTE)

        vnet = EcosystemVirtualNetwork(eco_id=self.eco_id, work=self.work / "vnet")
        vnet_state = vnet.start(selected)
        self.vnet = vnet

        started: dict[str, Any] = {}
        errors: list[str] = []
        for pid in selected:
            # Dock is modeled as peripheral attach target — still start a session so
            # dock attach/detach scenarios have a live LabSession.
            try:
                res = start_session(pid, repo_root=self.repo_root)
                iid = res.get("instance_id")
                if not iid:
                    errors.append(f"{pid}:no_instance")
                    started[pid] = {"ok": False, "error": "no_instance"}
                    continue
                self.member_instances[pid] = str(iid)
                started[pid] = {
                    "ok": bool(res.get("ok")),
                    "instance_id": iid,
                    "SKIPPED_ENVIRONMENT": bool(res.get("SKIPPED_ENVIRONMENT")),
                }
                if not res.get("ok") and not res.get("SKIPPED_ENVIRONMENT"):
                    errors.append(f"{pid}:start_failed")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{pid}:{exc}")
                started[pid] = {"ok": False, "error": str(exc)}

        self.started_at = time.time()
        self.running = True
        # Honest: multi-member sessions started ≠ ECO-010 soak complete.
        compute_ok = all(
            started.get(p, {}).get("ok") or started.get(p, {}).get("SKIPPED_ENVIRONMENT")
            for p in PRIMARY_COMPUTE
            if p in started
        )
        self.state = {
            "preset": self.preset,
            "topology": topo,
            "vnet": vnet_state,
            "members": started,
            "simultaneous_soak": False,
            "ECO_010_depth": "not_run",
            "errors": errors,
        }
        out = {
            "ok": bool(compute_ok and not errors),
            "eco_id": self.eco_id,
            "preset": self.preset,
            "member_instances": dict(self.member_instances),
            "state": self.state,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
            "SILICON_EXACT_EMULATION": False,
            "note": (
                "Ecosystem members started with isolated Lab vnet. "
                "Not ECO-010 full simultaneous soak; master complete remains false."
            ),
        }
        (self.work / "ecosystem.json").write_text(
            json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return out

    def status(self) -> dict[str, Any]:
        members = {}
        for pid, iid in self.member_instances.items():
            try:
                members[pid] = get_session(iid).status()
            except KeyError:
                members[pid] = {"ok": False, "error": "session_gone", "instance_id": iid}
        return {
            "ok": self.running,
            "eco_id": self.eco_id,
            "running": self.running,
            "uptime_s": (time.time() - self.started_at) if self.running else 0,
            "preset": self.preset,
            "member_instances": dict(self.member_instances),
            "members": members,
            "vnet": self.vnet.status() if self.vnet else None,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
            "SILICON_EXACT_EMULATION": False,
        }

    def graph(self) -> dict[str, Any]:
        nodes = []
        edges = []
        for pid, iid in self.member_instances.items():
            nodes.append({"id": pid, "instance_id": iid, "kind": "device"})
        # Continuity / dock / ring edges (logical topology).
        if "student_14_5" in self.member_instances and "dsxl_coder" in self.member_instances:
            edges.append({"from": "student_14_5", "to": "dsxl_coder", "kind": "continuity"})
        if "handheld_hybrid" in self.member_instances and "dock" in self.member_instances:
            edges.append({"from": "handheld_hybrid", "to": "dock", "kind": "dock_attach"})
        if "edge_io_rings" in self.member_instances:
            for tgt in ("student_14_5", "dsxl_coder"):
                if tgt in self.member_instances:
                    edges.append({"from": "edge_io_rings", "to": tgt, "kind": "ring_input"})
        return {
            "ok": True,
            "eco_id": self.eco_id,
            "nodes": nodes,
            "edges": edges,
            "vnet": self.vnet.status() if self.vnet else None,
            "schema": "gunnchos.device_lab.ecosystem_graph.v1",
        }

    def stop(self) -> dict[str, Any]:
        stopped = {}
        for pid, iid in list(self.member_instances.items()):
            try:
                stopped[pid] = stop_session(iid)
            except KeyError:
                stopped[pid] = {"ok": False, "error": "already_gone"}
        vnet_clean = self.vnet.cleanup() if self.vnet else {"ok": True, "skipped": True}
        self.running = False
        self.member_instances.clear()
        _ECOSYSTEMS.pop(self.eco_id, None)
        out = {
            "ok": True,
            "eco_id": self.eco_id,
            "stopped": stopped,
            "vnet_cleanup": vnet_clean,
        }
        (self.work / "ecosystem_stop.json").write_text(
            json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8"
        )
        return out


def start_ecosystem(
    *,
    repo_root: Path,
    preset: str = "full",
    members: list[str] | None = None,
) -> dict[str, Any]:
    eco_id = f"eco-{uuid.uuid4().hex[:8]}"
    work = lab_artifact_root(repo_root) / "ecosystem" / "runtimes" / eco_id
    rt = EcosystemRuntime(eco_id=eco_id, repo_root=repo_root, work=work, preset=preset)
    _ECOSYSTEMS[eco_id] = rt
    return rt.start(members=members)


def get_ecosystem(eco_id: str) -> EcosystemRuntime:
    if eco_id not in _ECOSYSTEMS:
        raise KeyError(eco_id)
    return _ECOSYSTEMS[eco_id]


def stop_ecosystem(eco_id: str) -> dict[str, Any]:
    return get_ecosystem(eco_id).stop()


def list_ecosystems() -> list[dict[str, Any]]:
    return [e.status() for e in _ECOSYSTEMS.values()]


def active_ecosystem() -> EcosystemRuntime | None:
    running = [e for e in _ECOSYSTEMS.values() if e.running]
    return running[-1] if running else None
