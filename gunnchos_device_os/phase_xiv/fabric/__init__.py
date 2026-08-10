"""gunnchFabric — capability discovery / trust / lease with camera+NPU fallback E2E."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FabricNode:
    node_id: str
    capabilities: set[str]
    trusted: bool = False
    npu: bool = False
    camera: bool = False


@dataclass
class Lease:
    lease_id: str
    capability: str
    provider: str
    consumer: str
    expires_at: float
    active: bool = True


class GunnchFabric:
    def __init__(self):
        self.nodes: dict[str, FabricNode] = {}
        self.leases: dict[str, Lease] = {}
        self.trust_log: list[dict[str, Any]] = []
        self.fallback_log: list[dict[str, Any]] = []

    def advertise(self, node_id: str, capabilities: set[str], *, npu: bool = False, camera: bool = False) -> FabricNode:
        node = FabricNode(node_id=node_id, capabilities=set(capabilities), npu=npu, camera=camera)
        self.nodes[node_id] = node
        return node

    def establish_trust(self, a: str, b: str) -> dict[str, Any]:
        if a not in self.nodes or b not in self.nodes:
            raise KeyError("unknown_node")
        self.nodes[a].trusted = True
        self.nodes[b].trusted = True
        entry = {"a": a, "b": b, "at": time.time(), "ok": True}
        self.trust_log.append(entry)
        return entry

    def discover(self, capability: str) -> list[str]:
        return [
            n.node_id
            for n in self.nodes.values()
            if capability in n.capabilities and n.trusted
        ]

    def lease(self, consumer: str, capability: str, *, ttl_s: float = 60.0) -> Lease:
        providers = self.discover(capability)
        if not providers:
            raise RuntimeError(f"no_provider:{capability}")
        provider = providers[0]
        lease_id = hashlib.sha256(f"{consumer}:{provider}:{capability}:{time.time()}".encode()).hexdigest()[:16]
        lease = Lease(
            lease_id=lease_id,
            capability=capability,
            provider=provider,
            consumer=consumer,
            expires_at=time.time() + ttl_s,
        )
        self.leases[lease_id] = lease
        return lease

    def revoke(self, lease_id: str) -> dict[str, Any]:
        lease = self.leases[lease_id]
        lease.active = False
        return {"ok": True, "lease_id": lease_id, "active": False}

    def camera_with_npu_fallback(self, consumer: str) -> dict[str, Any]:
        """E2E: prefer camera+NPU node; fall back to CPU vision if NPU absent."""
        npu_nodes = [
            n for n in self.nodes.values()
            if n.trusted and n.camera and n.npu and "vision.infer" in n.capabilities
        ]
        if npu_nodes:
            lease = self.lease(consumer, "vision.infer")
            result = {
                "ok": True,
                "path": "camera+npu",
                "lease_id": lease.lease_id,
                "provider": lease.provider,
            }
            self.fallback_log.append(result)
            return result
        cpu_nodes = [
            n for n in self.nodes.values()
            if n.trusted and n.camera and "vision.cpu" in n.capabilities
        ]
        if not cpu_nodes:
            # advertise ephemeral CPU fallback on consumer itself for digital proof
            self.advertise(f"{consumer}-cpu-fb", {"vision.cpu"}, camera=True, npu=False)
            self.nodes[f"{consumer}-cpu-fb"].trusted = True
            cpu_nodes = [self.nodes[f"{consumer}-cpu-fb"]]
        lease = self.lease(consumer, "vision.cpu")
        result = {
            "ok": True,
            "path": "camera+cpu_fallback",
            "lease_id": lease.lease_id,
            "provider": lease.provider,
            "npu_available": False,
        }
        self.fallback_log.append(result)
        return result

    def e2e(self) -> dict[str, Any]:
        self.advertise("dsxl-01", {"vision.infer", "vision.cpu", "display.share"}, npu=True, camera=True)
        self.advertise("handheld-01", {"input.gamepad", "vision.cpu"}, camera=True, npu=False)
        self.advertise("student-01", {"files.share", "ai.tutor"})
        self.establish_trust("dsxl-01", "handheld-01")
        self.establish_trust("dsxl-01", "student-01")
        # First path: NPU available
        npu_path = self.camera_with_npu_fallback("student-01")
        # Force fallback: revoke trust on NPU node camera path by removing npu node trust temporarily
        self.nodes["dsxl-01"].trusted = False
        fallback = self.camera_with_npu_fallback("handheld-01")
        self.nodes["dsxl-01"].trusted = True
        ok = npu_path["path"] == "camera+npu" and fallback["path"] == "camera+cpu_fallback"
        return {
            "ok": ok,
            "npu_path": npu_path,
            "fallback_path": fallback,
            "nodes": list(self.nodes),
            "leases_active": sum(1 for l in self.leases.values() if l.active),
        }
