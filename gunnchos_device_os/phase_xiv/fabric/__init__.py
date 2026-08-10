"""gunnchFabric — capability discovery / trust / lease with camera+NPU fallback E2E.

Trust is mutual and token-gated (digital). Unsigned advertise alone must not
grant leases. PHYSICAL_PENDING for production attestation / pairing.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
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
    enrollment_token: str = field(default="", repr=False)


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
        self.denials: list[dict[str, Any]] = []

    def advertise(
        self,
        node_id: str,
        capabilities: set[str],
        *,
        npu: bool = False,
        camera: bool = False,
        enrollment_token: str | None = None,
    ) -> FabricNode:
        token = enrollment_token or secrets.token_hex(16)
        node = FabricNode(
            node_id=node_id,
            capabilities=set(capabilities),
            npu=npu,
            camera=camera,
            enrollment_token=token,
        )
        self.nodes[node_id] = node
        return node

    def _token_ok(self, node_id: str, token: str) -> bool:
        node = self.nodes.get(node_id)
        if node is None or not token:
            return False
        return hmac.compare_digest(node.enrollment_token, token)

    def establish_trust(
        self,
        a: str,
        b: str,
        *,
        token_a: str | None = None,
        token_b: str | None = None,
    ) -> dict[str, Any]:
        """Mutual trust requires both enrollment tokens (no unilateral trust)."""
        if a not in self.nodes or b not in self.nodes:
            raise KeyError("unknown_node")
        if not token_a or not token_b:
            denial = {
                "ok": False,
                "reason": "missing_enrollment_tokens",
                "a": a,
                "b": b,
            }
            self.denials.append(denial)
            raise PermissionError("missing_enrollment_tokens")
        if not self._token_ok(a, token_a) or not self._token_ok(b, token_b):
            denial = {
                "ok": False,
                "reason": "bad_enrollment_token",
                "a": a,
                "b": b,
            }
            self.denials.append(denial)
            raise PermissionError("bad_enrollment_token")
        self.nodes[a].trusted = True
        self.nodes[b].trusted = True
        entry = {"a": a, "b": b, "at": time.time(), "ok": True, "mutual": True}
        self.trust_log.append(entry)
        return entry

    def discover(self, capability: str, *, requester: str | None = None) -> list[str]:
        if requester is not None:
            req = self.nodes.get(requester)
            if req is None or not req.trusted:
                self.denials.append(
                    {
                        "op": "discover",
                        "requester": requester,
                        "reason": "untrusted_requester",
                    }
                )
                return []
        return [
            n.node_id
            for n in self.nodes.values()
            if capability in n.capabilities and n.trusted
        ]

    def lease(
        self,
        consumer: str,
        capability: str,
        *,
        ttl_s: float = 60.0,
        consumer_token: str | None = None,
    ) -> Lease:
        consumer_node = self.nodes.get(consumer)
        if consumer_node is None:
            raise KeyError("unknown_consumer")
        if not consumer_node.trusted:
            self.denials.append(
                {"op": "lease", "consumer": consumer, "reason": "untrusted_consumer"}
            )
            raise PermissionError("untrusted_consumer")
        if consumer_token is not None and not self._token_ok(consumer, consumer_token):
            self.denials.append(
                {"op": "lease", "consumer": consumer, "reason": "bad_consumer_token"}
            )
            raise PermissionError("bad_consumer_token")
        providers = self.discover(capability, requester=consumer)
        if not providers:
            raise RuntimeError(f"no_provider:{capability}")
        provider = providers[0]
        lease_id = hashlib.sha256(
            f"{consumer}:{provider}:{capability}:{time.time()}".encode()
        ).hexdigest()[:16]
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
            n
            for n in self.nodes.values()
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
            n
            for n in self.nodes.values()
            if n.trusted and n.camera and "vision.cpu" in n.capabilities
        ]
        if not cpu_nodes:
            # advertise ephemeral CPU fallback on consumer itself for digital proof
            fb = self.advertise(f"{consumer}-cpu-fb", {"vision.cpu"}, camera=True, npu=False)
            # mutual trust with consumer using enrollment tokens
            self.establish_trust(
                consumer,
                fb.node_id,
                token_a=self.nodes[consumer].enrollment_token,
                token_b=fb.enrollment_token,
            )
            cpu_nodes = [self.nodes[fb.node_id]]
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
        dsxl = self.advertise(
            "dsxl-01", {"vision.infer", "vision.cpu", "display.share"}, npu=True, camera=True
        )
        handheld = self.advertise(
            "handheld-01", {"input.gamepad", "vision.cpu"}, camera=True, npu=False
        )
        student = self.advertise("student-01", {"files.share", "ai.tutor"})
        self.establish_trust(
            "dsxl-01",
            "handheld-01",
            token_a=dsxl.enrollment_token,
            token_b=handheld.enrollment_token,
        )
        self.establish_trust(
            "dsxl-01",
            "student-01",
            token_a=dsxl.enrollment_token,
            token_b=student.enrollment_token,
        )
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
